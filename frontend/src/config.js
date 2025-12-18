// In Vite, we use import.meta.env to access environment variables.
// They must start with VITE_ to be exposed.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

console.log("Current API URL:", API_BASE_URL);
console.log("Environment Mode:", import.meta.env.MODE);
