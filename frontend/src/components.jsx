import React, {useState} from 'react';
import {pageUrl} from './api';

export function Link({to, navigate, children, ...props}) {
  return <a href={to} {...props} onClick={event => {
    if (!event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) {
      event.preventDefault(); navigate(to);
    }
  }}>{children}</a>;
}

export function Heading({title, eyebrow, description, children}) {
  return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{description && <p className="muted">{description}</p>}</div>{children}</div>;
}
export const Badge = ({children, kind = ''}) => <span className={'badge ' + kind}>{children}</span>;
export const Empty = ({children}) => <div className="empty"><h3>Aucun élément à afficher</h3><p>{children}</p></div>;
export function Pagination({page, location, navigate}) {
  return <nav className="pagination" aria-label="Pagination">{page.number > 1 && <Link to={pageUrl(location, page.number - 1)} navigate={navigate}>← Précédent</Link>}<span>Page {page.number} / {page.pages}</span>{page.number < page.pages && <Link to={pageUrl(location, page.number + 1)} navigate={navigate}>Suivant →</Link>}</nav>;
}

export function Search({name, label, value, navigate, path}) {
  return <form className="search" onSubmit={e => {e.preventDefault(); const query = new URLSearchParams(new FormData(e.currentTarget)); navigate(path + '?' + query);}}><label htmlFor={name}>{label}</label><input id={name} name={name} defaultValue={value} /><button className="button">Rechercher</button></form>;
}

export function DynamicForm({schema, submit, label = 'Enregistrer'}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [validation, setValidation] = useState(null);
  async function save(event) {
    event.preventDefault();
    if (busy) return;
    const body = new FormData(event.currentTarget);
    setBusy(true); setError(''); setValidation(null);
    try { await submit(body); }
    catch (err) { setError(err.message); setValidation(err.data?.form); }
    finally { setBusy(false); }
  }
  return <form onSubmit={save} aria-busy={busy}>
    {error && <div role="alert" className="error">{error}</div>}
    {(validation || schema).errors?.map((message, i) => <p role="alert" className="error" key={i}>{message}</p>)}
    {schema.fields.map(field => {
      const errors = validation?.fields.find(f => f.name === field.name)?.errors || [];
      const props = {id: field.name, name: field.name, required: field.required, maxLength: field.maxLength || undefined, disabled: busy, 'aria-invalid': errors.length > 0, 'aria-describedby': field.name + '-help', defaultValue: field.multiple ? (field.value || []).map(String) : field.value ?? ''};
      return <div className="form-field" key={field.name}><label htmlFor={field.name}>{field.label}{field.required && <span aria-hidden="true"> *</span>}</label>
        {field.type === 'textarea' ? <textarea {...props} rows={field.name === 'evidence' ? 6 : 3} /> : field.type === 'select' ? <select {...props} multiple={field.multiple}>{field.choices.map(choice => <option key={choice.value} value={choice.value}>{choice.label}</option>)}</select> : <input {...props} type={field.type} autoComplete={field.type === 'password' ? 'new-password' : undefined} />}
        <div id={field.name + '-help'}>{field.help && <small className="helptext">{field.help}</small>}{errors.map((message, i) => <p className="error" role="alert" key={i}>{message}</p>)}</div>
      </div>;
    })}<button className="button" disabled={busy}>{busy ? 'Enregistrement…' : label}</button>
  </form>;
}

export function MissionRow({mission, navigate}) {
  return <Link className="list-row" to={'/missions/' + mission.id + '/'} navigate={navigate}><span className="square">▤</span><span className="grow"><strong>{mission.name}</strong><small>{mission.authorization} · {mission.starts_on} → {mission.ends_on}</small></span><Badge>{mission.status_label}</Badge></Link>;
}

export function Finding({test, editable, navigate}) {
  return <article className="panel padded finding"><div className="section-heading"><h2>{test.title}</h2><Badge kind={test.severity}>{test.severity_label}</Badge></div><p className="muted">{test.tool_label} {test.tool_version} · {test.target} · {new Date(test.performed_at).toLocaleString('fr-FR', {timeZone:'Africa/Lagos'})} · {test.author}</p><details><summary>Méthode et preuve</summary><h3>Méthode</h3><pre>{test.method}</pre><h3>Preuve</h3><pre>{test.evidence}</pre><p className="hash">SHA-256 : {test.evidence_sha256}</p></details><h3>Correction</h3><p className="preserve">{test.remediation}</p><p><Badge kind="neutral">{test.state_label}</Badge> {test.owner} · Échéance : {test.due_on}</p>{test.followups?.length > 0 && <><h3>Historique du suivi</h3>{test.followups.map((event, index) => <div className="followup" key={index}><p className="small muted">{new Date(event.created_at).toLocaleString('fr-FR', {timeZone:'Africa/Lagos'})} · {event.actor} · {event.state_label}</p><pre>{event.retest}</pre></div>)}</>}{editable && <Link to={'/tests/' + test.id + '/suivi/'} navigate={navigate}>Mettre à jour le suivi →</Link>}</article>;
}

export function Compliance({compact = false}) {
  const rows = [
    ['A.8.8', 'Vulnérabilités techniques', 'Cibles, constats, sévérité, responsable, échéance, correction et re-test.', 'Veille, inventaire des actifs, délais de traitement et acceptation des risques.'],
    ['A.8.25', 'Développement sécurisé', 'RBAC, sessions, validation des entrées, tests automatisés et guide de déploiement.', 'Politique de développement, revue de code, dépendances et séparation des environnements.'],
    ['A.8.29', 'Tests de sécurité', 'Méthode, version, date, preuve textuelle, empreinte et rapport exporté.', 'Plan de recette, critères d’acceptation et validation indépendante.'],
  ];
  if (compact) return <>{rows.map(row => <div className="control-row" key={row[0]}><b>{row[0].slice(2)}</b><div><strong>{row[1]}</strong><p>{row[2]}</p></div></div>)}</>;
  return <><Heading eyebrow="PRÉPARATION À L’AUDIT" title="Matrice de preuves ISO" description="Contribution technique aux contrôles ciblés d’ISO/IEC 27001:2022." /><div className="notice">L’application contribue à une démarche de management de la sécurité. Elle ne démontre pas, à elle seule, la conformité ni la certification de l’organisation.</div><section className="panel table-scroll"><table><thead><tr><th>Contrôle ciblé</th><th>Preuves fournies</th><th>Validation organisationnelle attendue</th></tr></thead><tbody>{rows.map(row => <tr key={row[0]}><td><strong>{row[0]}</strong><br/>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>)}</tbody></table></section><section className="panel padded spaced"><h2>Préparer le dossier d’audit</h2><ol><li>Vérifier l’autorisation écrite et le périmètre.</li><li>Revoir les constats, leurs preuves et corrections.</li><li>Exporter le rapport JSON et obtenir le journal auprès de l’administrateur.</li><li>Archiver les preuves et faire signer la décision de recette.</li></ol></section></>;
}
