from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from faker import Faker
import time
import datetime

faker = Faker()
from locust import HttpUser, TaskSet, task, between
import json

from requests.auth import HTTPBasicAuth

basic = HTTPBasicAuth("admin", "superSecretAdminPassword123")


class ApiLoadTesting(HttpUser):
    wait_time = between(0.1, 1)

    host = "http://localhost:8000"

    @task(1)
    def create_users(self):
        user = faker.profile()
        response = self.client.post(
            "/user-register",
            data=json.dumps(
                {
                    "username": user["username"],
                    "name": user["name"],
                    "birthdate": "2000-01-01T00:00:00",
                    "password": faker.password(),
                }
            ),
        )
        return response

    @task(2)
    def get_users(self):
        response = self.client.post(
            "/user-get",
            data=json.dumps(
                {
                    "id": faker.random_number(digits=3),
                }
            ),
            auth=basic,
        )
        return response

    @task(3)
    def promote_user(self):
        response = self.client.post(
            "/user-promote",
            data=json.dumps(
                {
                    "id": faker.random_number(digits=3),
                }
            ),
            auth=basic,
        )
        return response
