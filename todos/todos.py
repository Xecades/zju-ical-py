from dataclasses import dataclass
from datetime import datetime

from exam.exam import ExamTable
from ical.ical import Event


@dataclass
class Todo:
    course_name: str
    course_code: str
    title: str
    end_time: str

    def toEvent(self, exams: ExamTable) -> Event:
        end_dt = datetime.fromisoformat(self.end_time.replace("Z", "+00:00"))
        end_dt_local = end_dt.astimezone()

        description = f"课程: {self.course_name}\\n作业: {self.title}"

        if found_exams := exams.findByClassId(self.course_code[:22]):
            description += f"\\n学分: {found_exams[0].credit:.1f}"

        return Event(
            summary=f"{self.course_name} - {self.title}",
            location="",
            description=description,
            start=end_dt_local,
            end=None,
        )


class TodoTable:
    todos: list[Todo]

    def __init__(self):
        self.todos = []

    def fromRes(self, res: list[dict]) -> None:
        for item in res:
            if not item.get("is_student", False):
                continue

            todo = Todo(
                course_name=item["course_name"],
                course_code=item["course_code"],
                title=item["title"],
                end_time=item["end_time"],
            )
            self.todos.append(todo)

    def toEvents(self, exams: ExamTable) -> list[Event]:
        events = []
        for todo in self.todos:
            events.append(todo.toEvent(exams))
        return events
