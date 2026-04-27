from vibe_tool.parser import parse_js_file, parse_python_file, generate_file_description


def test_parse_js_export_functions():
    code = """
import { db } from '../db/schema';

export function getUser(id: string): User {
    return db.query(id);
}

export const deleteUser = async (id: string) => {
    await db.delete(id);
};

export class UserService {
    constructor(private db: DB) {}
}
"""
    result = parse_js_file(code, "src/services/user.ts")
    assert any("getUser" in e for e in result["exports"])
    assert any("deleteUser" in e for e in result["exports"])
    assert any("UserService" in e for e in result["exports"])
    assert any("db/schema" in d for d in result["dependencies"])


def test_parse_js_api_routes():
    code = """
import express from 'express';
const router = express.Router();

router.get('/users', listUsers);
router.post('/users', createUser);
router.get('/users/:id', getUser);
app.delete('/users/:id', deleteUser);
"""
    result = parse_js_file(code, "src/api/routes/users.ts")
    assert any("GET /users" in r for r in result["routes"])
    assert any("POST /users" in r for r in result["routes"])
    assert any("DELETE /users/:id" in r for r in result["routes"])


def test_parse_js_schema():
    code = """
export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    email: varchar('email', { length: 255 }),
    createdAt: timestamp('created_at').defaultNow(),
});

export const products = pgTable('products', {
    id: serial('id').primaryKey(),
    title: varchar('title'),
    price: integer('price'),
});
"""
    result = parse_js_file(code, "src/db/schema.ts")
    assert any("users" in t for t in result["tables"])
    assert any("products" in t for t in result["tables"])


def test_parse_python_functions():
    code = """
import os
from pathlib import Path
from fastapi import FastAPI

app = FastAPI()

def helper_internal():
    pass

class UserService:
    def get(self, id):
        pass

@app.get("/users")
def list_users():
    return []

@app.post("/users")
async def create_user(data: UserCreate):
    pass
"""
    result = parse_python_file(code, "src/main.py")
    assert any("helper_internal" in e for e in result["exports"])
    assert any("UserService" in e for e in result["exports"])
    assert any("GET /users" in r for r in result["routes"])
    assert any("POST /users" in r for r in result["routes"])
    assert any("pathlib" in d or "Path" in d for d in result["dependencies"])


def test_parse_python_models():
    code = """
from sqlalchemy import Column, Integer, String
from .base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    title = Column(String)
"""
    result = parse_python_file(code, "src/models.py")
    assert any("users" in t for t in result["tables"])
    assert any("products" in t for t in result["tables"])


def test_generate_file_description():
    parsed = {
        "exports": ["getUser(id: string)", "deleteUser(id: string)", "UserService"],
        "routes": [],
        "dependencies": ["../db/schema"],
        "tables": [],
    }
    desc = generate_file_description(parsed)
    assert "getUser" in desc
    assert "3" in desc or "exports" in desc.lower()
