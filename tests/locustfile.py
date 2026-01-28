from locust import HttpUser, TaskSet, task, between
import time


class AuthAPITasks(TaskSet):
    def on_start(self):
        """Setup: register a user for this taskset"""
        unique_id = f"{self.user.user_id}_{int(time.time())}"
        self.email = f"loadtest_{unique_id}@example.com"
        self.username = f"user_{unique_id}"
        self.password = "TestPass123!"

        self.client.post(
            "/auth/register",
            json={
                "email": self.email,
                "username": self.username,
                "password": self.password,
            },
        )

    @task(3)
    def login(self):
        self.client.post(
            "/auth/jwt/login",
            data={
                "username": self.email,
                "password": self.password,
            },
        )


class WebsiteUser(HttpUser):
    tasks = [AuthAPITasks]
    wait_time = between(1, 3)
    user_id = 0

    def on_start(self):
        WebsiteUser.user_id += 1
        self.user_id = WebsiteUser.user_id
