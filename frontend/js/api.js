// Talks to the backend. All data comes through here.

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function explain(detail) {
  // The backend sends either a sentence or a list of field problems.
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = (d.loc || []).slice(1).join(' › ');
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join('; ');
  }
  return typeof detail === 'string' ? detail : 'Something went wrong.';
}

async function request(method, path, { params, body } = {}) {
  const url = new URL(path, window.location.origin);
  for (const [key, value] of Object.entries(params || {})) {
    if (value !== null && value !== undefined && value !== '') url.searchParams.set(key, value);
  }
  let response;
  try {
    response = await fetch(url, {
      method,
      credentials: 'same-origin',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (networkProblem) {
    throw new ApiError(0, 'Cannot reach the server. Check your connection and try again.');
  }
  let data = null;
  try {
    data = await response.json();
  } catch (notJson) {
    /* some answers have no body */
  }
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      window.dispatchEvent(new Event('session-expired'));
    }
    throw new ApiError(response.status, explain(data && data.detail));
  }
  return data;
}

export const api = {
  get: (path, params) => request('GET', path, { params }),
  post: (path, body) => request('POST', path, { body: body || {} }),
  patch: (path, body) => request('PATCH', path, { body }),
  del: (path) => request('DELETE', path),
};
