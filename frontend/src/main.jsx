import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {request} from './api';
import {Link, Heading, Badge, Empty, Pagination, Search, DynamicForm, MissionRow, Finding, Compliance} from './components';
import './style.css';

const currentLocation = () => window.location.pathname + window.location.search;

function App() {
  const [location, setLocation] = useState(currentLocation);
  const [session, setSession] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState('');
  const [revision, setRevision] = useState(0);
  const [actionBusy, setActionBusy] = useState(false);
  const path = location.split('?')[0];
  function navigate(to) {
    if (!to.startsWith('/') || to.startsWith('//')) return;
    window.history.pushState({}, '', to); setLocation(currentLocation()); setRevision(r => r + 1);
    setData(null); setError(''); window.scrollTo(0, 0);
  }
  useEffect(() => {
    const pop = () => {setLocation(currentLocation()); setData(null);};
    window.addEventListener('popstate', pop);
    return () => window.removeEventListener('popstate', pop);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError('');
    (async () => {
      try {
        const info = await request('/session/', {signal: controller.signal});
        setSession(info);
        if (!info.user) {
          if (path !== '/connexion/') navigate('/connexion/');
          return;
        }
        if (path === '/connexion/') {navigate('/'); return;}
        const result = await request(location, {signal: controller.signal});
        setData(result);
      } catch (err) {
        if (err.name === 'AbortError') return;
        if (err.status === 401) {setSession(null); navigate('/connexion/');}
        else setError(err.message);
      } finally {if (!controller.signal.aborted) setLoading(false);}
    })();
    return () => controller.abort();
  }, [location, revision]);

  async function mutate(body, target = path) {
    try {
      const result = await request(target, {body, csrfToken: session.csrfToken});
      if (target !== '/connexion/' && target !== '/deconnexion/') setNotice('Modification enregistrée.');
      if (result.redirect) navigate(result.redirect);
      else setRevision(r => r + 1);
    } catch (err) {
      if (err.status === 401 && target !== '/connexion/') {setSession(null); navigate('/connexion/');}
      throw err;
    }
  }
  async function action(target) {
    setActionBusy(true);
    try {await mutate(new FormData(), target);} catch (err) {setNotice(err.message);} finally {setActionBusy(false);}
  }
  async function download(target, filename) {
    try {
      const result = await request(target);
      const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], {type:'application/json'}));
      const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {if (err.status === 401) navigate('/connexion/'); else setNotice(err.message);}
  }
  if (!session?.user) {
    if (loading) return <div className="login-body"><p role="status">Chargement de votre espace…</p></div>;
    if (error) return <div className="login-body"><div role="alert" className="error">{error}<button onClick={() => setRevision(r => r + 1)}>Réessayer</button></div></div>;
    return <Login submit={body => mutate(body, '/connexion/')} />;
  }
  const nav = [['/', '◫', 'Vue d’ensemble'], ['/missions/', '▤', 'Missions d’audit'], ['/outils/', '⌘', 'Bibliothèque d’outils'], ...(session.current_role !== 'Pentesteur' ? [['/journal/', '≡', 'Journal d’activité']] : []), ['/conformite/', '◇', 'Contrôles ISO'], ...(session.is_manager ? [['/utilisateurs/', '♙', 'Utilisateurs']] : [])];
  const shared = {navigate, session, mutate, download, action, actionBusy, location};
  return <><aside className="sidebar"><Link className="brand" to="/" navigate={navigate}><span className="brand-icon">A</span>AuditHub<span className="brand-dot">.</span></Link><p className="nav-label">ESPACE DE TRAVAIL</p><nav aria-label="Navigation principale">{nav.map(([to, icon, label]) => <Link key={to} to={to} navigate={navigate} aria-current={(to === '/' ? path === '/' : path.startsWith(to)) ? 'page' : undefined}><span aria-hidden="true">{icon}</span> <span>{label}</span></Link>)}</nav><div className="sidebar-bottom"><span className="status-dot"/>Espace de tests autorisés</div></aside><div className="workspace"><header className="topbar"><span>Plateforme de sécurité / Audit technique</span><div className="account"><span className="avatar">{session.user.username[0]?.toUpperCase()}</span><span>{session.user.username}<small>{session.current_role || 'Sans rôle'}</small></span><button className="text-button" disabled={actionBusy} onClick={() => action('/deconnexion/')}>Déconnexion</button></div></header><main>{notice && <div className="notice" role="status">{notice}<button className="text-button" aria-label="Fermer la notification" onClick={() => setNotice('')}>×</button></div>}{loading ? <p className="panel empty" role="status">Chargement…</p> : error ? <section className="panel padded"><p className="error" role="alert">{error}</p><button className="button" onClick={() => setRevision(r => r + 1)}>Réessayer</button></section> : data && <Page key={location + ':' + revision} path={path} data={data} {...shared}/>}</main><footer>AuditHub · Gestion des tests d’intrusion<span>Traçabilité · Maîtrise des accès · Preuves</span></footer></div></>;
}

function Login({submit}) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function login(event) {
    event.preventDefault(); const body = new FormData(event.currentTarget);
    setBusy(true); setError('');
    try {await submit(body);} catch (err) {setError(err.message);} finally {setBusy(false);}
  }
  return <div className="login-body"><main className="login-card"><div className="brand"><span className="brand-icon">A</span>AuditHub.</div><p className="eyebrow">ESPACE D’AUDIT TECHNIQUE</p><h1>Bienvenue dans votre<br/>espace sécurisé.</h1><p className="muted">Connectez-vous pour accéder à vos missions et aux preuves de test.</p>{error && <p role="alert" className="error">{error}</p>}<form onSubmit={login}><label htmlFor="username">Identifiant</label><input id="username" name="username" autoComplete="username" required maxLength={150} disabled={busy}/><label htmlFor="password">Mot de passe</label><input id="password" name="password" type="password" autoComplete="current-password" required disabled={busy}/><button className="button full" disabled={busy}>{busy ? 'Connexion…' : 'Se connecter →'}</button></form><p className="small muted">Accès nominatif · Les connexions sont journalisées.<br/>Contactez votre administrateur pour obtenir un compte.</p></main></div>;
}

function Page({path, data, navigate, session, mutate, download, action, actionBusy, location}) {
  const {is_manager: manager, can_write: canWrite} = session;
  if (path === '/') return <><Heading eyebrow="VOTRE ESPACE DE TRAVAIL" title="Vue d’ensemble" description="Pilotez vos tests. Documentez vos preuves. Préparez vos audits.">{manager && <Link className="button" to="/missions/nouvelle/" navigate={navigate}>+ Nouvelle mission</Link>}</Heading><div className="hero"><div><span className="pill">AUDIT TECHNIQUE</span><h2>Une vision claire de votre<br/>posture de sécurité.</h2><p>Retrouvez vos missions, vos outils et le suivi des corrections<br/>dans un espace partagé et traçable.</p><Link className="button light" to="/missions/" navigate={navigate}>Consulter les missions ↗</Link></div><div className="hero-art" aria-hidden="true"><div className="orbit"><div className="shield">✓</div></div><span>A.8.8 · A.8.25 · A.8.29</span></div></div><div className="metrics">{[['Missions accessibles',data.mission_count,'Périmètres documentés'],['Tests documentés',data.test_count,'Preuves enregistrées'],['Constats ouverts',data.open_count,'Corrections à suivre'],['Priorité haute / critique',data.critical_count,'Constats non résolus']].map(([label, count, caption]) => <article key={label}><span>{label}</span><strong>{String(count).padStart(2,'0')}</strong><small>{caption}</small></article>)}</div><div className="columns"><section className="panel"><div className="section-heading"><h2>Missions récentes</h2><Link to="/missions/" navigate={navigate}>Tout voir →</Link></div>{data.missions.length ? data.missions.map(mission => <MissionRow key={mission.id} mission={mission} navigate={navigate}/>) : <Empty>Un administrateur définit le périmètre et les habilitations de votre première mission.</Empty>}</section><section className="panel"><div className="section-heading"><h2>Cadre de contrôle</h2><Badge kind="neutral">ISO 27001:2022</Badge></div><Compliance compact/><Link className="panel-link" to="/conformite/" navigate={navigate}>Consulter la matrice de preuves →</Link></section></div><section className="panel"><div className="section-heading"><h2>Derniers résultats</h2><span className="muted small">Tests exécutés hors plateforme</span></div>{data.tests.length ? data.tests.map(test => <Link className="list-row" key={test.id} to={'/missions/'+test.mission+'/'} navigate={navigate}><span className="grow"><strong>{test.title}</strong><small>{test.tool_label} · {test.target}</small></span><Badge kind={test.severity}>{test.severity_label}</Badge></Link>) : <Empty>Documentez un premier test pour voir ses résultats ici.</Empty>}</section></>;

  if (path === '/outils/') return <><Heading eyebrow="BOÎTE À OUTILS" title="Bibliothèque d’outils" description="Quatre outils, un même processus de documentation."/><div className="notice">Mode documentaire : exécutez les outils dans votre laboratoire autorisé, puis consignez leurs résultats. Aucun scan n’est lancé depuis cette interface.</div><div className="tool-grid">{data.tools.map(([number,name,category,description,key]) => <article className="panel tool-card" key={key}><div className="tool-top"><span className="tool-number">{number}</span><Badge kind="neutral">Résultats manuels</Badge></div><p className="eyebrow">{category}</p><h2>{name}</h2><p className="muted">{description}</p><Link className="panel-link" to="/missions/" navigate={navigate}>Choisir une mission →</Link></article>)}</div></>;

  if (path === '/missions/') return <><Heading eyebrow="PÉRIMÈTRES & AUTORISATIONS" title="Missions d’audit" description="Seules les missions auxquelles vous avez accès sont affichées.">{manager && <Link className="button" to="/missions/nouvelle/" navigate={navigate}>+ Nouvelle mission</Link>}</Heading><Search name="q" label="Rechercher une mission" value={data.query} navigate={navigate} path={path}/><section className="panel">{data.page.items.length ? data.page.items.map(mission => <MissionRow key={mission.id} mission={mission} navigate={navigate}/>) : <Empty>Créez une mission ou demandez votre habilitation.</Empty>}</section><Pagination page={data.page} location={location} navigate={navigate}/></>;

  if (data.mission) {
    const mission = data.mission;
    return <><Heading eyebrow={'MISSION #' + mission.id + ' · ' + mission.status_label} title={mission.name} description={mission.starts_on + ' → ' + mission.ends_on}><button className="button secondary" onClick={() => download(path + 'rapport/', 'mission-' + mission.id + '.json')}>↓ Exporter le rapport JSON</button></Heading><section className="panel padded"><h2>Périmètre autorisé</h2><p>Autorisation : <strong>{mission.authorization}</strong></p><pre>{mission.scope}</pre><p className="small muted">Les nouveaux résultats doivent respecter le périmètre et la période autorisée.</p><div className="actions">{canWrite && mission.status === 'active' && <Link className="button" to={path+'test/'} navigate={navigate}>+ Documenter un test</Link>}{manager && <button className="button secondary" disabled={actionBusy} onClick={() => action(path+'statut/')}>{mission.status === 'active' ? 'Clôturer' : 'Réouvrir'} la mission</button>}</div></section><h2 className="spaced">Résultats & suivi des corrections</h2>{data.tests.length ? data.tests.map(test => <Finding key={test.id} test={test} editable={canWrite && mission.status === 'active'} navigate={navigate}/>) : <section className="panel"><Empty>Consignez la méthode, la preuve et les corrections après un test autorisé.</Empty></section>}</>;
  }
  if (path === '/utilisateurs/') return <><Heading eyebrow="CONTRÔLE DES ACCÈS" title="Utilisateurs & rôles" description="Comptes nominatifs et habilitations par mission."/><div className="columns"><section className="panel padded"><h2>Créer un compte</h2><DynamicForm schema={data.form} submit={mutate} label="Créer le compte"/></section><section className="panel"><div className="section-heading"><h2>Comptes existants</h2></div>{data.users.map(user => <div className="list-row" key={user.id}><span className="avatar">{user.username[0]?.toUpperCase()}</span><span className="grow"><strong>{user.username}</strong><small>{user.role || 'Sans rôle'}</small></span><Badge kind="neutral">{user.is_active ? 'Actif' : 'Désactivé'}</Badge>{!user.is_superuser && <Link to={'/utilisateurs/'+user.id+'/acces/'} navigate={navigate}>Gérer</Link>}</div>)}</section></div></>;

  if (data.form) { const back = path.startsWith('/utilisateurs/') ? '/utilisateurs/' : '/missions/'; return <><Heading eyebrow="DOCUMENTATION D’AUDIT" title={data.title} description={data.subtitle}/><section className="panel form-panel"><DynamicForm schema={data.form} submit={mutate}/><Link className="back-link" to={back} navigate={navigate}>← Retour</Link></section></>; }

  if (path === '/journal/') return <><Heading eyebrow="TRAÇABILITÉ" title="Journal d’activité" description={manager ? 'Événements de la plateforme.' : 'Vos événements personnels.'}>{manager && <button className="button secondary" onClick={() => download('/journal/export/', 'journal-audit.json')}>↓ Exporter JSON</button>}</Heading><Search name="action" label="Filtrer par action" value={data.action} navigate={navigate} path={path}/><section className="panel table-scroll"><table><thead><tr>{['Date','Acteur','Action','Objet','Adresse IP'].map(x => <th key={x}>{x}</th>)}</tr></thead><tbody>{data.page.items.map(event => <tr key={event.id}><td>{new Date(event.timestamp).toLocaleString('fr-FR',{timeZone:'Africa/Lagos'})}</td><td>{event.actor}</td><td><code>{event.action}</code><details><summary>Détails</summary><pre>{JSON.stringify(event.detail,null,2)}</pre></details></td><td>{event.object_ref}</td><td>{event.ip}</td></tr>)}{!data.page.items.length && <tr><td colSpan={5}>Aucun événement pour ce filtre.</td></tr>}</tbody></table></section><Pagination page={data.page} location={location} navigate={navigate}/><p className="small muted">Archivage externe nécessaire pour une conservation inviolable.</p></>;
  if (path === '/conformite/') return <Compliance/>;
  return <p role="alert">Page introuvable.</p>;
}

class ErrorBoundary extends React.Component {
  state = {error: false};
  static getDerivedStateFromError() {return {error: true};}
  render() {return this.state.error ? <main><p className="error" role="alert">Impossible d’afficher cette page.</p><button className="button" onClick={() => window.location.reload()}>Recharger</button></main> : this.props.children;}
}
createRoot(document.getElementById('root')).render(<ErrorBoundary><App/></ErrorBoundary>);
