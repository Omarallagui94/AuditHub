export class ApiError extends Error {
  constructor(status, data) {
    super(data.error || (status === 422 ? 'Vérifiez les champs du formulaire.' : 'La requête a échoué.'));
    this.status = status;
    this.data = data;
  }
}

export async function request(path, {body, csrfToken, signal} = {}) {
  const response = await fetch('/api' + path, {
    method: body ? 'POST' : 'GET', credentials: 'same-origin', signal,
    headers: {Accept: 'application/json', ...(body ? {'X-CSRFToken': csrfToken} : {})},
    body,
  });
  const data = await response.json().catch(() => ({error: 'Réponse inattendue du serveur.'}));
  if (!response.ok) throw new ApiError(response.status, data);
  return data;
}

export function pageUrl(location, number) {
  const url = new URL(location, 'http://localhost');
  url.searchParams.set('page', number);
  return url.pathname + url.search;
}
