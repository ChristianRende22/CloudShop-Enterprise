/**
 * Envoltorio delgado sobre amazon-cognito-identity-js.
 *
 * Usa authenticateUser() -> flujo SRP por defecto (ALLOW_USER_SRP_AUTH debe
 * estar habilitado en el App Client, ver infra/terraform/cognito.tf). La
 * propia librería persiste la sesión (tokens) en localStorage bajo las claves
 * CognitoIdentityServiceProvider.<clientId>.*, por eso getSession() sigue
 * funcionando después de refrescar la página sin que nosotros manejemos storage.
 */
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute,
} from "amazon-cognito-identity-js";

const poolData = {
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
};

export const userPool = new CognitoUserPool(poolData);

export function signUp(email, password, role) {
  return new Promise((resolve, reject) => {
    const attributes = [
      new CognitoUserAttribute({ Name: "email", Value: email }),
      new CognitoUserAttribute({ Name: "custom:role", Value: role }),
    ];
    userPool.signUp(email, password, attributes, null, (err, result) => {
      if (err) return reject(err);
      resolve(result);
    });
  });
}

export function confirmSignUp(email, code) {
  const user = new CognitoUser({ Username: email, Pool: userPool });
  return new Promise((resolve, reject) => {
    user.confirmRegistration(code, true, (err, result) => {
      if (err) return reject(err);
      resolve(result);
    });
  });
}

export function resendConfirmationCode(email) {
  const user = new CognitoUser({ Username: email, Pool: userPool });
  return new Promise((resolve, reject) => {
    user.resendConfirmationCode((err, result) => {
      if (err) return reject(err);
      resolve(result);
    });
  });
}

export function signIn(email, password) {
  const user = new CognitoUser({ Username: email, Pool: userPool });
  const authDetails = new AuthenticationDetails({
    Username: email,
    Password: password,
  });
  return new Promise((resolve, reject) => {
    user.authenticateUser(authDetails, {
      onSuccess: (session) => resolve(session),
      onFailure: (err) => reject(err),
    });
  });
}

export function signOut() {
  const user = userPool.getCurrentUser();
  if (user) user.signOut();
}

/** Devuelve la sesión activa (o null) validando/renovando el token si hace falta. */
export function getSession() {
  const user = userPool.getCurrentUser();
  if (!user) return Promise.resolve(null);
  return new Promise((resolve) => {
    user.getSession((err, session) => {
      if (err || !session || !session.isValid()) return resolve(null);
      resolve(session);
    });
  });
}

/** Claims normalizados del idToken: sub, email, custom:role. */
export function claimsFromSession(session) {
  if (!session) return null;
  const payload = session.getIdToken().payload;
  return {
    sub: payload.sub,
    email: payload.email,
    role: payload["custom:role"] || "Cliente",
  };
}

export async function getIdToken() {
  const session = await getSession();
  return session ? session.getIdToken().getJwtToken() : null;
}
