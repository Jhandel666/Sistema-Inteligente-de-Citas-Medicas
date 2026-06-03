export const getTokenPayload = () => {
  const token = localStorage.getItem("access_token");

  if (!token) return null;

  try {
    const payload = token.split(".")[1];
    const decoded = atob(payload);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
};

export const getUserRole = () => {
  const payload = getTokenPayload();
  return payload?.role || payload?.user_role || "recepcion";
};

export const isAdmin = () => {
  return getUserRole() === "admin";
};

export const isReception = () => {
  return getUserRole() === "recepcion";
};

export const getUserName = () => {
  const payload = getTokenPayload();
  return payload?.name || "Usuario";
};