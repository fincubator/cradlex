from aiogram.utils.callback_data import CallbackData

edit_task_step = CallbackData("edit_task_step", "step")
edit_worker_step = CallbackData("edit_worker_step", "step")
take_task = CallbackData("take_task", "task_id")
task_timeliness = CallbackData("task_timeliness", "timeliness")
review_task = CallbackData("check_task", "task_id", "review")
