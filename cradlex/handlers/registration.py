import phonenumbers
import sqlalchemy as sa
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.emoji import emojize

from cradlex import database
from cradlex import models
from cradlex import states
from cradlex.bot import dp
from cradlex.filters import OperatorFilter
from cradlex.i18n import _


@dp.message_handler(~OperatorFilter(), state=states.Registration.first_message)
async def first_message(message: types.Message, state: FSMContext):
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard_markup.add(
        types.KeyboardButton(
            emojize(":telephone_receiver: ") + _("send_contact"), request_contact=True
        )
    )
    await states.Registration.contact.set()
    await message.answer(_("first_message"), reply_markup=keyboard_markup)


async def set_phone(
    phone: phonenumbers.PhoneNumber, message: types.Message, state: FSMContext
):
    async with database.sessionmaker() as session:
        async with session.begin():
            worker_cursor = await session.execute(
                sa.update(models.Worker)
                .where(
                    models.Worker.phone
                    == phonenumbers.format_number(
                        phone, phonenumbers.PhoneNumberFormat.E164
                    ),
                )
                .values(id=message.from_user.id)
                .returning(models.Worker.name)
            )
            worker = worker_cursor.one_or_none()
    if worker is None:
        await message.answer(_("worker_not_found"))
    else:
        await state.finish()
        await message.answer(
            _("welcome_message {name}").format(name=worker.name),
            reply_markup=types.ReplyKeyboardRemove(),
        )


@dp.message_handler(
    content_types=types.ContentType.CONTACT, state=states.Registration.contact
)
async def set_phone_from_contact(message: types.Message, state: FSMContext):
    await set_phone(
        phonenumbers.parse(message.contact.phone_number, region="RU"), message, state
    )


@dp.message_handler(state=states.Registration.contact)
async def set_phone_from_text(message: types.Message, state: FSMContext):
    try:
        number = phonenumbers.parse(message.text, region="RU")
    except phonenumbers.NumberParseException:
        await message.answer(_("contact_parse_error"))
    else:
        await set_phone(number, message, state)
