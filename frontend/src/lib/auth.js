// frontend/src/lib/auth.js
import api from "./axios";

export function getAuth() {
  const token = localStorage.getItem("access_token");
  const user = JSON.parse(localStorage.getItem("auth_user") || "null");
  return { token, user };
}

export async function login({ email, password }) {
  const { data } = await api.post("/users/login", {
    user_email: email,
    user_password: password,
  });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("auth_user", JSON.stringify(data.user));
  return data.user;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("auth_user");
}
