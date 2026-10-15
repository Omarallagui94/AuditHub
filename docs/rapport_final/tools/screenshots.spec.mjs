import playwright from '../../../frontend/node_modules/@playwright/test/index.js';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const {test, expect} = playwright;

const here = path.dirname(fileURLToPath(import.meta.url));
const output = path.resolve(here, '../figures/screenshots');
const shot = (page, name) => page.screenshot({path: path.join(output, name), fullPage: true});

async function login(page) {
  await page.goto('/connexion/');
  await page.getByLabel('Identifiant', {exact: true}).fill('admin-test');
  await page.getByLabel('Mot de passe').fill('Browser-Tests-Only!294');
  await page.getByRole('button', {name: 'Se connecter'}).click();
  await expect(page.getByRole('heading', {name: 'Vue d’ensemble', exact: true})).toBeVisible();
}

test('captures authentiques du rapport', async ({page}) => {
  await page.goto('/connexion/');
  await expect(page.getByRole('button', {name: 'Se connecter'})).toBeVisible();
  await shot(page, '01-connexion.png');
  await login(page);

  await page.getByRole('link', {name: '+ Nouvelle mission'}).click();
  await shot(page, '02-creation-mission.png');
  await page.getByLabel('Nom de la mission').fill('Audit de démonstration');
  await page.getByLabel('Référence').fill('AUT-DEMO-2026');
  await page.getByLabel('Périmètre').fill('192.0.2.0/24\n2001:db8::/64');
  await page.getByLabel('Début').fill('2020-01-01');
  await page.getByLabel('Fin', {exact: false}).fill('2099-12-31');
  await page.getByLabel('Utilisateurs habilités').selectOption([{label: 'tester-test'}, {label: 'auditor-test'}]);
  await page.getByRole('button', {name: 'Enregistrer', exact: true}).click();

  await page.getByRole('link', {name: 'Documenter un test'}).click();
  await page.getByLabel('Outil', {exact: false}).selectOption('nmap');
  await page.getByLabel('Version utilisée').fill('7.95');
  await page.getByLabel('IP de la cible').fill('192.0.2.20');
  await page.getByLabel('Titre du constat').fill('Service HTTP à durcir');
  await page.getByLabel('Date du test').fill('2026-10-15T10:00');
  await page.getByLabel('Méthode et paramètres').fill('Inventaire contrôlé des services exposés dans le périmètre autorisé.');
  await page.getByLabel('Preuve textuelle').fill('Port 80/tcp ouvert ; en-têtes de sécurité à vérifier.');
  await page.getByLabel('Sévérité').selectOption('medium');
  await page.getByLabel('Mesure corrective').fill('Forcer HTTPS et revoir les en-têtes de réponse.');
  await page.getByLabel('Responsable').fill('Équipe infrastructure');
  await page.getByLabel('Échéance').fill('2026-11-15');
  await shot(page, '03-saisie-resultat.png');
  await page.getByRole('button', {name: 'Enregistrer', exact: true}).click();
  await page.getByText('Méthode et preuve', {exact: true}).click();
  await shot(page, '04-detail-mission.png');

  await page.getByRole('link', {name: 'Mettre à jour le suivi'}).click();
  await page.getByLabel('État').selectOption('resolved');
  await page.getByLabel('Preuve de re-test').fill('Re-test documentaire : redirection HTTPS et en-têtes contrôlés.');
  await page.getByRole('button', {name: 'Enregistrer', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Historique du suivi'})).toBeVisible();
  await shot(page, '05-historique-suivi.png');

  await page.getByRole('link', {name: 'Vue d’ensemble'}).click();
  await expect(page.getByRole('heading', {name: 'Vue d’ensemble', exact: true})).toBeVisible();
  await shot(page, '06-tableau-de-bord.png');
  await page.getByRole('link', {name: 'Utilisateurs', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Utilisateurs & rôles'})).toBeVisible();
  await shot(page, '07-utilisateurs-roles.png');
  await page.getByRole('link', {name: 'Journal d’activité'}).click();
  await expect(page.getByRole('heading', {name: 'Journal d’activité'})).toBeVisible();
  await shot(page, '08-journal.png');
  await page.getByRole('link', {name: 'Contrôles ISO'}).click();
  await expect(page.getByRole('heading', {name: 'Matrice de preuves ISO'})).toBeVisible();
  await shot(page, '09-controles-iso.png');
});
