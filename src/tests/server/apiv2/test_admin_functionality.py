import json
from typing import List
import uuid

from random import randint, choices
from string import ascii_lowercase

from tests.server.apiv2 import APIV2Test

from server.extensions import guard, db
from server.models.tasks import CeleryTask
from server.models.users import User


class TaskManagementTests(APIV2Test):
    """Tests for user functionality"""

    def setUp(self):
        super().setUp()
        # Add test user
        self._admin = User(
            username="test_admin",
            password=guard.hash_password("12345"),
            email="test_admin@test.com",
            roles="admin,operator",
        )
        db.session.add(self._admin)
        db.session.commit()
        # login with user
        res = self.client.post(
            "/api/v2/login",
            data=json.dumps(dict(identifier="test_admin", password="12345")),
            content_type="application/json",
        )
        # set token and header
        self._token = res.json.get("access_token")
        self._header = {"Authorization": f"Bearer {self._token}"}
        self.tasks = self.generate_random_tasks()
    
    def generate_random_tasks(self)->List[str]:
        tasks = []
        for _ in range(10):
            t_id = str(uuid.uuid4())
            ctask = CeleryTask(
                source="source",
                destination="dest",
                log_path=f"/var/log/pymap/{t_id}",
                task_id=t_id,
                n_accounts=randint(1,100),
                owner_username="".join(choices(ascii_lowercase, k=randint(6,10)))
            )
            tasks.append(ctask)
            db.session.add(ctask)
            db.session.commit()
        return tasks
    
    def test_delete_tasks(self):
        # Post a request to delete self.tasks[0] and self.tasks[1]
        res = self.client.post(
            "/api/v2/admin/delete-tasks",
            data=json.dumps(dict(task_ids=[self.tasks[0].task_id, self.tasks[1].task_id])),
            content_type="application/json",
            headers=self._header
        )

        self.assert200(res)
        # Get ids in message
        ids = [t_id for t_id in res.json["message"]]
        assert self.tasks[0].task_id in ids
        assert self.tasks[1].task_id in ids
        # Verify if task was removed from DB
        assert CeleryTask.query.filter_by(task_id=self.tasks[0].task_id).first() is None
        assert CeleryTask.query.filter_by(task_id=self.tasks[1].task_id).first() is None


    def test_delete_no_ids(self):
        res = self.client.post(
            "/api/v2/admin/delete-tasks",
            data=json.dumps(dict(task_ids=[])),
            content_type="application/json",
            headers=self._header
        )

        self.assert400(res)
