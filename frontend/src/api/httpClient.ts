import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || window.location.origin;

const httpClient = axios.create({
  baseURL,
});

httpClient.interceptors.request.use((config) => {
  const password = localStorage.getItem("app_password");
  if (password) {
    config.headers = config.headers || {};
    config.headers["X-App-Password"] = password;
  }
  return config;
});

export default httpClient;
