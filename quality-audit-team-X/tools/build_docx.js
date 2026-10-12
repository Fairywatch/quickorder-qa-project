// Génère le document Word d'audit qualité QuickOrder.
// Les chiffres et les preuves proviennent de la campagne réellement exécutée.
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType,
  PageBreak, Header, Footer, PageNumber, TableOfContents, LevelFormat,
  convertInchesToTwip,
} = require('docx');

const ROOT = path.join(__dirname, '..');
const data = JSON.parse(fs.readFileSync(
  path.join(ROOT, 'docs', 'evidence', 'docx-data.json'), 'utf8'));

// ------------------------------------------------------------------ palette
// Rendu sobre : pas de couleur, pas de trame, pas de liseré décoratif.
// Seuls restent le noir, un gris pour le texte secondaire, et la grille
// des tableaux, qui porte de l'information.
const INK = '000000', MUTED = '595959', ACCENT = '000000';
const FAIL = '000000', PASS = '000000', WARN = '000000';
const HEAD_BG = null, ZEBRA = null, CODE_BG = null;
const FAIL_BG = null, PASS_BG = null;

const W = convertInchesToTwip(6.5) * 20 / 20; // largeur utile en DXA
const FULL = 9360; // 6.5" en DXA

// ------------------------------------------------------------------ helpers
const t = (text, o = {}) => new TextRun({ text, ...o });

function p(text, o = {}) {
  const { bold, italics, color, size, align, spacing, indent, bullet, numbering } = o;
  return new Paragraph({
    children: Array.isArray(text) ? text
      : [t(text, { bold, italics, color, size: size || 20 })],
    alignment: align, spacing: spacing || { after: 110 },
    indent, bullet, numbering,
  });
}

const h1 = (text) => new Paragraph({
  text, heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 170 },
});
const h2 = (text) => new Paragraph({
  text, heading: HeadingLevel.HEADING_2,
  spacing: { before: 260, after: 120 },
});
const h3 = (text) => new Paragraph({
  text, heading: HeadingLevel.HEADING_3,
  spacing: { before: 180, after: 90 },
});

const li = (text, o = {}) => new Paragraph({
  children: Array.isArray(text) ? text : [t(text, { size: 20, ...o })],
  bullet: { level: o.level || 0 }, spacing: { after: 70 },
});

const numli = (text, ref) => new Paragraph({
  children: Array.isArray(text) ? text : [t(text, { size: 20 })],
  numbering: { reference: ref, level: 0 }, spacing: { after: 70 },
});

function code(text) {
  // La chasse fixe suffit à distinguer une preuve du texte courant.
  return String(text).split('\n').map((line, i, arr) => new Paragraph({
    children: [t(line || ' ', { font: 'Consolas', size: 15, color: INK })],
    spacing: { after: i === arr.length - 1 ? 110 : 0, line: 220 },
    indent: { left: 280, right: 170 },
  }));
}

function cell(children, o = {}) {
  return new TableCell({
    width: { size: o.w, type: WidthType.DXA },
    margins: { top: 70, bottom: 70, left: 100, right: 100 },
    columnSpan: o.span,
    verticalAlign: 'top',
    children: Array.isArray(children) ? children : [children],
  });
}

function tbl(widths, headers, rows, o = {}) {
  const head = new TableRow({
    tableHeader: true,
    children: headers.map((htxt, i) => cell(
      new Paragraph({
        children: [t(htxt, { bold: true, size: 17, color: ACCENT })],
        spacing: { after: 0 },
      }), { w: widths[i] })),
  });
  const body = rows.map((r) => new TableRow({
    children: r.map((c, i) => {
      const isObj = c && typeof c === 'object' && !Array.isArray(c);
      const txt = isObj ? c.text : c;
      return cell(new Paragraph({
        children: [t(String(txt), {
          size: 18, bold: isObj ? c.bold : false,
          color: isObj && c.color ? c.color : INK,
          font: isObj && c.mono ? 'Consolas' : undefined,
        })],
        spacing: { after: 0 },
      }), { w: widths[i] });
    }),
  }));
  return new Table({
    columnWidths: widths,
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    rows: [head, ...body],
    margins: { top: 40, bottom: 40 },
  });
}

const spacer = (after = 160) => new Paragraph({ text: '', spacing: { after } });

// champ d'une fiche : libellé + valeur
function field(label, value, o = {}) {
  return new Paragraph({
    children: [
      t(label + ' : ', { bold: true, size: 18, color: MUTED }),
      t(String(value), { size: 18, color: o.color || INK, bold: o.bold }),
    ],
    spacing: { after: 60 },
    indent: { left: 170 },
  });
}

const SEV_COLOR = {
  Bloquante: FAIL, Critique: FAIL, Majeure: WARN, Mineure: MUTED,
};

// ------------------------------------------------------------------ contenu
const S = data.stats;
const kids = [];

// ---------- page de titre
kids.push(spacer(1700));
kids.push(p('AUDIT QUALITÉ', {
  align: AlignmentType.CENTER, bold: true, size: 26, color: ACCENT,
  spacing: { after: 90 },
}));
kids.push(p('QuickOrder V3.1', {
  align: AlignmentType.CENTER, bold: true, size: 64, spacing: { after: 120 },
}));
kids.push(p('Campagne de test et recommandation de mise en production', {
  align: AlignmentType.CENTER, size: 24, color: MUTED, spacing: { after: 520 },
}));

kids.push(tbl([2400, 4000], ['Élément', 'Valeur'], [
  ['Application testée', 'QuickOrder V3.1'],
  ['Environnement', 'Docker Compose — http://127.0.0.1:5000'],
  ['Date de campagne', '22 septembre 2026'],
  ['Cas de test exécutés', `${S.total} / ${S.total}`],
  ['Résultat', { text: `${S.pass} Pass — ${S.fail} Fail`, bold: true }],
  ['Anomalies identifiées', `${data.bugs.length} (1 bloquante, 4 critiques)`],
  ['Recommandation', { text: 'NO-GO', bold: true, color: FAIL }],
]));

kids.push(spacer(400));
kids.push(p([t('Pour chaque anomalie déclarée dans ce document, le lecteur trouvera '
  + 'la requête HTTP que nous avons envoyée et la réponse que l\'application nous a '
  + 'renvoyée. Rien n\'est supposé.', { size: 19, italics: true, color: MUTED })],
{ align: AlignmentType.CENTER }));

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ---------- sommaire
kids.push(h1('Sommaire'));
kids.push(new TableOfContents('Sommaire', {
  hyperlink: true, headingStyleRange: '1-2',
}));
kids.push(new Paragraph({ children: [new PageBreak()] }));

// ---------- synthèse
kids.push(h1('Synthèse'));

kids.push(p([
  t('Recommandation : ', { size: 22 }),
  t('NO-GO', { size: 22, bold: true, color: FAIL }),
]));
kids.push(p('Nous déconseillons la mise en production en l\'état. Cinq anomalies '
  + 'bloquantes ou critiques touchent le parcours de commande et de paiement, et elles '
  + 'se déclenchent en usage normal : aucune manipulation particulière n\'est '
  + 'nécessaire pour les reproduire. Mettre le produit en production exposerait '
  + 'l\'entreprise à un litige financier dès les premières commandes.'));

kids.push(h3('Chiffres de la campagne'));
kids.push(tbl([2600, 1500, 1200, 1200, 1400],
  ['Catégorie', 'Cas', 'Pass', 'Fail', 'Réussite'],
  [
    ...S.parCategorie.map((c) => [
      c.nom,
      { text: c.total, mono: true },
      { text: c.pass, mono: true, color: c.pass ? PASS : MUTED },
      { text: c.fail, mono: true, color: c.fail ? FAIL : MUTED, bold: !!c.fail },
      { text: `${Math.round(c.pass / c.total * 100)} %`, mono: true },
    ]),
    [
      { text: 'Total', bold: true, fill: HEAD_BG },
      { text: S.total, mono: true, bold: true, fill: HEAD_BG },
      { text: S.pass, mono: true, bold: true, fill: HEAD_BG },
      { text: S.fail, mono: true, bold: true, fill: HEAD_BG },
      { text: `${Math.round(S.pass / S.total * 100)} %`, mono: true, bold: true, fill: HEAD_BG },
    ],
  ]));
kids.push(spacer(90));
kids.push(p('Blocked : 0 — Skipped : 0. Taux d\'exécution : 100 %, aucun cas n\'a été '
  + 'bloqué.', { size: 18, color: MUTED }));

kids.push(h3('Ce que montre la campagne'));
kids.push(p('QuickOrder affiche ses règles métier (montant minimum, restaurant fermé, '
  + 'produit en rupture, promotion à 15 %) mais n\'en contrôle aucune au moment où le '
  + 'client s\'engage financièrement.'));
kids.push(p('Le résultat est nettement coupé en deux, et c\'est le principal '
  + 'enseignement de la campagne. La couche technique passe 30 tests sur 30 : '
  + 'authentification, validation des formats, codes HTTP, cloisonnement des comptes. '
  + 'Les 16 cas de règles métier, eux, échouent sans une seule exception.'));
kids.push(p('C\'est une bonne nouvelle pour la remédiation : il s\'agit d\'ajouter des '
  + 'contrôles, pas de refondre l\'application.'));

kids.push(h3('Quelques écarts entre l\'affichage et le comportement réel'));
kids.push(tbl([3100, 5100], ['Règle affichée au client', 'Comportement réel constaté'], [
  ['« Minimum 25,00 € » sur Couscous Atlas', 'Commande de 3,50 € acceptée'],
  ['« FERMÉ » sur Night Sushi', 'Commande acceptée et marquée payée'],
  ['« HORS STOCK » sur le Veggie Burger', 'Ajout au panier accepté, stock descendu à −20'],
  ['« 15 % de réduction avec ATLAS15 »', '10 % appliqués'],
  ['Paiement espèces de 1,00 € pour 6,69 € dus', 'Commande marquée payée, rendu de −5,69 €'],
  ['Un paiement PayPal = une commande', { text: 'Deux commandes créées, sur les deux canaux', bold: true }],
]));

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================ 1. STRATÉGIE
kids.push(h1('1. Stratégie de test'));
kids.push(p('Nous devons évaluer la qualité de QuickOrder avant sa mise en production '
  + 'et rendre une recommandation Go ou No-Go, appuyée sur des preuves que n\'importe '
  + 'qui peut rejouer. Il ne s\'agit pas de corriger l\'application : il s\'agit de '
  + 'démontrer ses défauts.'));

kids.push(h2('1.1 Périmètre'));
kids.push(h3('Dans le périmètre'));
[
  'Catalogue : page d\'accueil, recherche, filtres (catégorie, frais de livraison, végétarien), tri',
  'Fiche restaurant : affichage du menu, état ouvert/fermé, affichage du stock',
  'Panier : ajout, modification de quantité, suppression, règle « un seul restaurant »',
  'Tunnel de commande : checkout, adresse, coupons, moyens de paiement (carte, PayPal, espèces)',
  'Compte client : inscription, connexion, déconnexion, profil, adresses',
  'Commandes : historique, détail, annulation, recommande',
  'Avis et favoris',
  'Back-office : tableau de bord administrateur, changement de statut des commandes',
  'API REST : les 11 endpoints /api/*, authentification par en-tête X-API-Key',
  'Règles métier : montant minimum, stock, restaurant fermé, coupons, cycle de vie des commandes',
].forEach((x) => kids.push(li(x)));

kids.push(h3('Hors périmètre'));
kids.push(tbl([2900, 5300], ['Exclusion', 'Justification'], [
  ['Performance et charge', 'Aucun objectif de performance spécifié ; environnement local mono-conteneur non représentatif'],
  ['Audit de sécurité approfondi', 'Hors mandat ; seuls les contrôles d\'accès fonctionnels sont vérifiés'],
  ['Multi-navigateurs et mobile', 'Aucune matrice de navigateurs cibles fournie'],
  ['Accessibilité (RGAA / WCAG)', 'Non demandé dans le brief, à prévoir dans un second audit'],
  ['Intégration réelle des paiements', 'Les paiements sont simulés, aucun prestataire n\'est connecté'],
  ['E-mails et notifications', 'Fonctionnalité absente de l\'application'],
  ['Tests utilisateurs', 'Non réalisés — voir la section 6'],
]));

kids.push(h2('1.2 Parcours critiques'));
kids.push(p('Classés par impact business décroissant. Ce sont eux qui concentrent '
  + 'l\'effort de test.'));
kids.push(tbl([700, 2500, 5000], ['#', 'Parcours', 'Pourquoi il est critique'], [
  ['PC1', 'Commander et payer', 'Seul parcours générant du chiffre d\'affaires. Toute anomalie s\'y traduit directement en perte d\'argent ou en litige client.'],
  ['PC2', 'Cohérence du stock', 'Une commande acceptée sur un produit indisponible est une commande non livrable : remboursement, perte de confiance.'],
  ['PC3', 'Disponibilité du restaurant', 'Une commande vers un restaurant fermé ne sera jamais préparée.'],
  ['PC4', 'Calcul du montant', 'Une erreur de calcul est une perte financière directe, dans un sens ou dans l\'autre.'],
  ['PC5', 'Authentification et cloisonnement', 'Accès aux commandes ou aux données d\'un autre client : incident RGPD.'],
  ['PC6', 'Découverte du catalogue', 'Sans découverte fiable, le client n\'atteint jamais le parcours d\'achat.'],
  ['PC7', 'Back-office : suivi des commandes', 'Le pilotage opérationnel dépend de la fiabilité des statuts.'],
]));

kids.push(h2('1.3 Risques et matrice risque × impact'));
kids.push(p('Criticité = probabilité × impact. Échelles : probabilité de 1 (rare) à '
  + '3 (usage normal) ; impact de 1 (gêne) à 4 (perte systématique ou risque '
  + 'juridique).'));
kids.push(tbl([650, 2750, 750, 800, 750, 1150, 1310],
  ['ID', 'Risque', 'Prob.', 'Impact', 'Score', 'Criticité', 'Anomalie'], [
    ['R1', 'Double facturation du client', '3', '4', { text: '12', bold: true }, { text: 'Critique', color: FAIL, bold: true }, 'BUG-005'],
    ['R2', 'Commande encaissée mais non livrable', '3', '4', { text: '12', bold: true }, { text: 'Critique', color: FAIL, bold: true }, 'BUG-002/003'],
    ['R3', 'Encaissement inférieur au montant dû', '2', '3', '6', { text: 'Critique', color: FAIL, bold: true }, 'BUG-006'],
    ['R4', 'Manipulation des montants par le client', '2', '3', '6', { text: 'Critique', color: FAIL, bold: true }, 'BUG-010'],
    ['R5', 'Publicité mensongère sur une promotion', '3', '2', '6', { text: 'Majeur', color: WARN }, 'BUG-007'],
    ['R6', 'Données de stock incohérentes', '3', '2', '6', { text: 'Majeur', color: WARN }, 'BUG-004'],
    ['R7', 'Montant minimum non respecté', '3', '2', '6', { text: 'Majeur', color: WARN }, 'BUG-001'],
    ['R8', 'Faux avis dégradant la confiance', '2', '2', '4', { text: 'Majeur', color: WARN }, 'BUG-011'],
    ['R9', 'Statuts de commande incohérents', '2', '2', '4', { text: 'Majeur', color: WARN }, 'BUG-012'],
    ['R10', 'Recherche et filtres erronés', '3', '1', '3', 'Modéré', 'BUG-008/009'],
    ['R11', 'Données non commandables exposées', '2', '1', '2', 'Modéré', 'BUG-013'],
  ]));
kids.push(spacer(90));
kids.push(p('R3 et R4 obtiennent un score de 6 mais sont remontés en criticité '
  + '« Critique » : ils portent sur l\'encaissement et sur l\'intégrité des montants, '
  + 'où aucune tolérance n\'est acceptable avant une mise en production.',
{ size: 18, italics: true, color: MUTED }));
kids.push(spacer(90));
kids.push(p('Les 11 risques identifiés se sont tous matérialisés durant la campagne. '
  + 'Aucun n\'est resté théorique.', { bold: true }));

kids.push(h2('1.4 Types de tests retenus'));
kids.push(tbl([2500, 5700], ['Type', 'Mise en œuvre'], [
  ['Fonctionnels boîte noire', 'Cœur de la campagne : l\'application est sollicitée par ses interfaces réelles (HTTP), sans dépendre de son code'],
  ['Cas nominaux', 'Vérifient que le parcours standard fonctionne (8 cas)'],
  ['Cas aux limites', 'Bornes des intervalles : quantités 0/1/20/21, montants 19,99/20,00, stock exact, mot de passe 7/8 (10 cas)'],
  ['Cas d\'erreur', 'Entrées invalides, ressources absentes, authentification et droits (12 cas)'],
  ['Règles métier', 'Confrontation du comportement réel aux règles annoncées par le produit (16 cas)'],
  ['Tests d\'API REST', 'Endpoints /api/*, codes HTTP, schémas de réponse, authentification par clé'],
  ['Tests d\'interface web', 'Parcours réels avec gestion de session et de cookies'],
  ['Tests croisés UI / API', 'Un même défaut est recherché sur les deux canaux (RM05 et RM16 pour PayPal)'],
  ['Non-régression', 'Le harnais est rejouable à l\'identique pour revalider les correctifs'],
]));

kids.push(h2('1.5 Priorisation risque × impact'));
kids.push(tbl([1400, 3600, 3200], ['Priorité', 'Cible', 'Cas concernés'], [
  ['P0', 'PC1 à PC4 : paiement, stock, restaurant fermé, calculs', 'RM01–RM08, RM14–RM16, N04, N06'],
  ['P1', 'PC5 : authentification, droits, cloisonnement', 'E01, E02, E05, E09, E10, RM10'],
  ['P2', 'Robustesse des entrées et bornes', 'L01–L10, E03, E04, E06–E08, E11, E12'],
  ['P3', 'PC6, PC7 : catalogue et back-office', 'RM09, RM11, RM12, RM13, N01'],
]));

kids.push(h2('1.6 Critères de décision'));
kids.push(li([t('No-Go', { bold: true, size: 20 }), t(' si au moins une anomalie bloquante ou critique touche un parcours critique (PC1 à PC5)', { size: 20 })]));
kids.push(li([t('Go sous conditions', { bold: true, size: 20 }), t(' si seules des anomalies majeures ou mineures subsistent, avec correctifs planifiés', { size: 20 })]));
kids.push(li([t('Go', { bold: true, size: 20 }), t(' si aucune anomalie de sévérité supérieure à mineure ne subsiste', { size: 20 })]));

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================ 2. CAS DE TEST
kids.push(h1('2. Cas de test'));
kids.push(p('Le brief demandait au minimum 24 cas (6 par catégorie). '
  + `${S.total} cas ont été écrits et exécutés, avec un minimum de 8 par catégorie. `
  + 'Chaque cas porte les neuf champs requis : identifiant, titre, objectif, '
  + 'préconditions, données, étapes, résultat attendu, résultat obtenu et statut.'));

kids.push(h2('2.1 Répartition'));
kids.push(tbl([2600, 1300, 1300, 1300, 1700],
  ['Catégorie', 'Préfixe', 'Cas', 'Pass', 'Fail'],
  S.parCategorie.map((c, i) => [
    c.nom, ['N', 'L', 'E', 'RM'][i],
    { text: c.total, mono: true },
    { text: c.pass, mono: true, color: c.pass ? PASS : MUTED },
    { text: c.fail, mono: true, color: c.fail ? FAIL : MUTED, bold: !!c.fail },
  ])));

const CAT_ORDER = ['Cas nominaux', 'Cas aux limites', 'Cas d\'erreur', 'Règles métier'];
const CAT_KEY = { 'Cas nominaux': 'Nominal', 'Cas aux limites': 'Limite', 'Cas d\'erreur': 'Erreur', 'Règles métier': 'Règle métier' };

CAT_ORDER.forEach((label, idx) => {
  const list = data.tests.filter((x) => x.categorie === CAT_KEY[label]);
  kids.push(h2(`2.${idx + 2} ${label}`));
  list.forEach((tc) => {
    const ko = tc.statut === 'Fail';
    kids.push(new Paragraph({
      children: [
        t(tc.id, { bold: true, size: 20, color: ACCENT, font: 'Consolas' }),
        t('   ' + tc.titre, { bold: true, size: 20 }),
        t('   [' + tc.statut.toUpperCase() + ']', {
          bold: true, size: 18, color: ko ? FAIL : PASS,
        }),
      ],
      spacing: { before: 190, after: 70 },
      keepNext: true,
    }));
    kids.push(field('Objectif', tc.objectif));
    kids.push(field('Préconditions', tc.preconditions));
    kids.push(field('Données', tc.donnees));
    kids.push(field('Étapes', tc.etapes));
    kids.push(field('Résultat attendu', tc.attendu));
    kids.push(field('Résultat obtenu', tc.obtenu, { color: ko ? FAIL : INK, bold: ko }));
    kids.push(field('Statut', tc.statut + (tc.bug ? ` — voir ${tc.bug}` : ''),
      { color: ko ? FAIL : PASS, bold: true }));
  });
});

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================ 3. CAMPAGNE
kids.push(h1('3. Campagne de test'));

kids.push(h2('3.1 Méthode'));
[
  ['Tests boîte noire.', ' L\'application est sollicitée par ses interfaces réelles (HTTP), sans dépendre de son code interne.'],
  ['Double canal.', ' Les défauts sensibles sont recherchés à la fois sur l\'interface web et sur l\'API. Le doublon PayPal est ainsi prouvé par RM05 (API) et RM16 (web).'],
  ['Preuve systématique.', ' Chaque anomalie cite la requête envoyée et la réponse reçue.'],
  ['Base réinitialisée', ' avant chaque exécution, pour garantir la reproductibilité.'],
  ['Contrôles positifs.', ' Certains tests incluent un cas témoin pour écarter les faux positifs : BUG-009 vérifie d\'abord que la recherche « pizza » fonctionne avant de conclure que « romaines » échoue.'],
].forEach(([b, r]) => kids.push(li([t(b, { bold: true, size: 20 }), t(r, { size: 20 })])));

kids.push(h2('3.2 Outils utilisés'));
kids.push(tbl([2700, 5500], ['Outil', 'Usage'], [
  ['Navigateur et DevTools', 'Parcours web, inspection des réponses et du DOM'],
  ['Swagger UI (/docs/)', 'Exploration de l\'API, bouton Authorize avec la clé quickorder-demo-key'],
  ['Harnais Python (requests)', 'Exécution des 46 cas, gestion de session et de cookies, capture des preuves'],
  ['Docker Compose', 'Déploiement et réinitialisation de la base entre les campagnes'],
]));

kids.push(h2('3.3 Reproductibilité'));
kids.push(p('La campagne est intégralement rejouable en deux commandes. Chaque '
  + 'exécution régénère le journal de preuves et les résultats.'));
kids.push(...code(
  '# 1. Démarrer QuickOrder sur une base propre\n'
  + 'cd quickorder-qa-project\n'
  + 'docker compose down -v && docker compose up -d\n'
  + '\n'
  + '# 2. Lancer la campagne complète\n'
  + 'cd quality-audit-team-X\n'
  + 'python tools/run_campaign.py'));
kids.push(p([
  t('Résultat attendu sur la version auditée : ', { size: 20 }),
  t(`${S.pass} Pass / ${S.fail} Fail`, { size: 20, bold: true }),
  t('. Après correction, le critère de succès est ', { size: 20 }),
  t(`${S.total} Pass / 0 Fail`, { size: 20, bold: true }),
  t('.', { size: 20 }),
]));

kids.push(h2('3.4 Sur la fiabilité de nos propres chiffres'));
kids.push(p('Notre harnais de test a lui-même eu deux défauts, découverts en cours de '
  + 'campagne. Le premier, un sélecteur de messages d\'alerte mal écrit, produisait '
  + 'quatre faux échecs : L10, E05, E07 et E10. Le second, un sélecteur de noms de '
  + 'restaurants, rendait inexploitables les preuves de RM08 et RM09.'));
kids.push(p('Nous les avons corrigés, puis rejoué la campagne entière sur une base '
  + 'remise à zéro. Tous les chiffres de ce document viennent de cette dernière '
  + 'exécution. Nous le mentionnons parce qu\'un résultat de test ne vaut que ce que '
  + 'vaut l\'instrument qui l\'a produit.'));

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================ 4. ANOMALIES
kids.push(h1('4. Bug reports'));
kids.push(p('Le brief demandait au minimum 8 bug reports reproductibles. '
  + `${data.bugs.length} anomalies distinctes ont été identifiées. Les ${S.fail} cas `
  + 'en échec se rattachent à ces anomalies, certaines étant prouvées sur les deux '
  + 'canaux.'));

kids.push(h2('4.1 Tableau de synthèse'));
kids.push(tbl([1250, 4300, 1300, 900, 1450],
  ['ID', 'Titre', 'Sévérité', 'Priorité', 'Cas de test'],
  data.bugs.map((b) => [
    { text: b.id, mono: true, bold: true },
    b.titre,
    { text: b.severite, color: SEV_COLOR[b.severite], bold: b.severite !== 'Mineure' },
    { text: b.priorite.split(' ')[0], mono: true },
    { text: b.cas.join(', '), mono: true },
  ])));
kids.push(spacer(90));
kids.push(tbl([2400, 1400], ['Sévérité', 'Nombre'],
  S.severites.map((s) => [
    { text: s.nom, color: SEV_COLOR[s.nom] },
    { text: s.n, mono: true, bold: true },
  ])));

data.bugs.forEach((b, i) => {
  kids.push(new Paragraph({ children: [new PageBreak()] }));
  kids.push(h2(`4.${i + 2} ${b.id} — ${b.titre}`));

  kids.push(tbl([1900, 6300], ['Champ', 'Valeur'], [
    ['Identifiant', { text: b.id, mono: true, bold: true }],
    ['Sévérité', { text: b.severite, color: SEV_COLOR[b.severite], bold: true }],
    ['Priorité', b.priorite],
    ['Risque couvert', `${b.risque} (voir section 1.3)`],
    ['Cas de test', { text: b.cas.join(', '), mono: true }],
    ['Version', 'QuickOrder V3.1 (Docker)'],
    ['Environnement', 'http://127.0.0.1:5000 — base réinitialisée'],
    ['Date de détection', '22/09/2026'],
    ['Statut', 'Ouvert'],
  ]));

  kids.push(h3('Contexte'));
  kids.push(p(b.contexte));

  kids.push(h3('Préconditions'));
  b.preconditions.forEach((x) => kids.push(li(x)));

  kids.push(h3('Étapes de reproduction'));
  b.etapes.forEach((x) => kids.push(numli(x, `steps-${b.id}`)));

  kids.push(h3('Résultat attendu'));
  kids.push(p(b.attendu));

  kids.push(h3('Résultat obtenu'));
  kids.push(p(b.obtenu));

  kids.push(h3('Preuve'));
  kids.push(p('Requêtes réellement envoyées et réponses réellement reçues, extraites '
    + 'du journal d\'exécution de la campagne.', { size: 18, italics: true, color: MUTED }));
  b.preuves.forEach((pr) => {
    kids.push(p(`Cas ${pr.cas} — ${pr.titre}`, { size: 18, bold: true, color: MUTED }));
    kids.push(...code(pr.texte));
  });

  kids.push(h3('Impact'));
  kids.push(p(b.impact));
});

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================ 5. ANALYSE
kids.push(h1('5. Analyse de campagne'));

kids.push(h2('5.1 Résultats chiffrés'));
kids.push(tbl([4200, 4000], ['Indicateur', 'Valeur'], [
  ['Nombre de tests exécutés', { text: S.total, mono: true, bold: true }],
  ['Pass', { text: `${S.pass} (${Math.round(S.pass / S.total * 100)} %)`, mono: true, color: PASS, bold: true }],
  ['Fail', { text: `${S.fail} (${Math.round(S.fail / S.total * 100)} %)`, mono: true, color: FAIL, bold: true }],
  ['Blocked', { text: S.blocked, mono: true }],
  ['Skipped', { text: S.skipped, mono: true }],
  ['Taux d\'exécution', '100 % — aucun cas bloqué'],
  ['Anomalies distinctes', { text: data.bugs.length, mono: true, bold: true }],
]));

kids.push(h2('5.2 Principaux risques'));
kids.push(p('Les risques ci-dessous sont avérés, pas hypothétiques : chacun s\'appuie '
  + 'sur une preuve reproductible.'));
kids.push(tbl([1300, 2900, 4000], ['Niveau', 'Risque', 'Conséquence concrète'], [
  [{ text: 'Critique', color: FAIL, bold: true }, 'Double facturation (BUG-005)', 'Chaque paiement PayPal crée deux commandes. Le client est débité deux fois et le restaurant prépare deux fois.'],
  [{ text: 'Critique', color: FAIL, bold: true }, 'Commande non livrable (BUG-002, BUG-003)', 'Le client paie pour un restaurant fermé ou un produit en rupture. Remboursement systématique.'],
  [{ text: 'Critique', color: FAIL, bold: true }, 'Encaissement insuffisant (BUG-006)', 'Commande livrée mais non payée, avec un rendu de monnaie négatif enregistré en base.'],
  [{ text: 'Critique', color: FAIL, bold: true }, 'Manipulation des montants (BUG-010)', 'Le montant est pris tel quel depuis le client : remise indue obtenue sans outil particulier.'],
  [{ text: 'Majeur', color: WARN }, 'Publicité trompeuse (BUG-007)', 'Écart de 5 points entre la promotion affichée et la remise accordée.'],
  [{ text: 'Majeur', color: WARN }, 'Intégrité des données (BUG-004)', 'Stocks négatifs : données inexploitables pour le réapprovisionnement.'],
  [{ text: 'Majeur', color: WARN }, 'Rentabilité des commandes (BUG-001)', 'Le minimum négocié avec les restaurants partenaires n\'est jamais appliqué.'],
  [{ text: 'Majeur', color: WARN }, 'Fiabilité des notes (BUG-011)', 'Avis manipulables, alors que la note est le critère de tri par défaut du catalogue.'],
  [{ text: 'Majeur', color: WARN }, 'Pilotage opérationnel (BUG-012)', 'Les statuts de commande ne reflètent plus la réalité.'],
  ['Modéré', 'Découverte du catalogue (BUG-008, BUG-009)', 'Le filtre prix retourne l\'inverse de la demande ; la recherche ne couvre pas l\'offre décrite.'],
]));

kids.push(h2('5.3 Ce qui fonctionne'));
kids.push(p('Ne retenir que les échecs donnerait une image fausse du produit. Les '
  + 'fondations suivantes sont solides et ne demandent aucune reprise :'));
[
  'Authentification API — clé absente ou invalide rejetée en HTTP 401 (E01, E02)',
  'Cloisonnement des comptes — Bob ne peut pas consulter la commande d\'Alice (E10)',
  'Cloisonnement des rôles — un client ne peut pas accéder au back-office (E09)',
  'Validation des entrées — quantités hors bornes, types incorrects, paiements inconnus rejetés en HTTP 400 (L03, L04, E11, E12)',
  'Bornes des intervalles — quantités 1 et 20 acceptées, 0 et 21 refusées',
  'Règles de coupons — seuil minimum à la borne exacte, plafond de remise, coupon expiré (L05, L06, L07, E06)',
  'Politique de mot de passe — 7 caractères refusés, 8 acceptés (L09, L10)',
  'Règle « un panier = un restaurant » — mélange refusé (E08)',
  'Parcours nominal complet — de l\'accueil à la confirmation de commande (N01 à N08)',
].forEach((x) => kids.push(li(x)));
kids.push(p('Cela change la nature du travail de remédiation : les correctifs '
  + 'consistent à ajouter des contrôles métier, pas à refondre l\'application. '
  + 'L\'architecture, elle, tient.'));

kids.push(h2('5.4 Recommandation Go / No-Go'));
kids.push(p([
  t('Décision : ', { size: 22 }),
  t('NO-GO', { size: 22, bold: true, color: FAIL }),
]));
kids.push(p('Le critère de décision défini en section 1.6 est le suivant : No-Go si au '
  + 'moins une anomalie bloquante ou critique touche un parcours critique. Ce critère '
  + 'est atteint cinq fois :'));
[
  'BUG-005 (bloquante) — double facturation sur tout paiement PayPal, sur les deux canaux',
  'BUG-002 (critique) — commande acceptée chez un restaurant fermé',
  'BUG-003 (critique) — commande acceptée sur un produit en rupture',
  'BUG-006 (critique) — commande livrée sans encaissement suffisant',
  'BUG-010 (critique) — montants manipulables depuis le client',
].forEach((x) => kids.push(numli(x, 'nogo')));
kids.push(p('Ces cinq anomalies touchent toutes PC1 (commander et payer), le seul '
  + 'parcours qui génère du chiffre d\'affaires. Elles se déclenchent en usage normal, '
  + 'sans manipulation experte. Une mise en production exposerait l\'entreprise à un '
  + 'litige financier dès les premières commandes.'));

kids.push(h3('Conditions de levée du No-Go'));
kids.push(tbl([1900, 3600, 2700], ['Étape', 'Condition', 'Anomalies concernées'], [
  [{ text: '1 — Obligatoire', bold: true }, 'Correction des anomalies bloquantes et critiques', 'BUG-005, BUG-002, BUG-003, BUG-006, BUG-010'],
  [{ text: '2 — Obligatoire', bold: true }, 'Revalidation complète : les 46 cas rejoués, 46 Pass attendus', 'Campagne entière'],
  [{ text: '3 — Recommandé', bold: true }, 'Correction des anomalies majeures', 'BUG-001, BUG-004, BUG-007, BUG-011, BUG-012'],
  [{ text: '4 — Planifiable', bold: true }, 'Anomalies mineures dans une itération ultérieure', 'BUG-008, BUG-009, BUG-013'],
]));
kids.push(spacer(90));
kids.push(p('Un Go sous conditions serait envisageable après les étapes 1 à 3, à '
  + 'condition de désactiver le moyen de paiement PayPal tant que BUG-005 n\'est pas '
  + 'revalidé en production.'));

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================ 6. NON RÉALISÉ
kids.push(h1('6. Tests utilisateurs'));
kids.push(new Paragraph({
  children: [t('Section non réalisée', { bold: true, size: 22, color: WARN })],
  spacing: { after: 130 },
}));
kids.push(p('Cette section du brief demandait de faire jouer au moins trois scénarios '
  + 'par au moins deux personnes réelles, puis de documenter pour chacune le profil, '
  + 'le contexte, le problème rencontré, sa fréquence, son impact, un verbatim, une '
  + 'hypothèse d\'amélioration et une priorité.'));
kids.push(p('Nous ne l\'avons pas réalisée : elle demande des participants humains, '
  + 'que nous n\'avons pas pu mobiliser dans le cadre de cette campagne. Ce document '
  + 'ne contient donc aucune conclusion sur l\'ergonomie ressentie.'));
kids.push(p('Nous préférons le dire plutôt que de le masquer. Présenter des retours '
  + 'utilisateurs fictifs aurait contredit le principe même de cet audit, qui est de '
  + 'ne rien affirmer sans preuve.'));

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================ 7. PLAN
kids.push(h1('7. Plan d\'amélioration'));
kids.push(p('Le brief demandait au minimum six améliorations priorisées et justifiées. '
  + 'Dix sont proposées, pour un effort total estimé à environ 17 jours-homme. Aucune '
  + 'ne propose de refonte : la campagne a montré que l\'architecture tient et que ce '
  + 'sont les contrôles métier qui manquent.'));

const AMEL = [
  ['AM-1', 'Rendre la création de commande idempotente', 'P0', '2 j·h', 'BUG-005',
    'Supprimer la duplication PayPal, puis introduire une clé d\'idempotence et une contrainte d\'unicité en base.',
    'L\'idempotence est la protection standard des systèmes de paiement : elle protège au-delà du défaut actuel (double-clic, réémission réseau, rejeu d\'une requête). Corriger la seule duplication laisserait ces cas ouverts.'],
  ['AM-2', 'Centraliser la validation métier de la commande', 'P0', '3 j·h', 'BUG-001, 002, 003, 006',
    'Créer une fonction unique de validation appelée par les deux canaux : restaurant ouvert, montant minimum, produit disponible, stock suffisant, espèces suffisantes.',
    'Centraliser importe plus que corriger. Les quatre règles manquaient sur les deux canaux : tant que chaque canal implémente ses propres contrôles, l\'écart se reproduira à la prochaine évolution.'],
  ['AM-3', 'Recalculer les montants côté serveur', 'P0', '2 j·h', 'BUG-010, BUG-006',
    'Ne jamais accepter un montant venant du client comme base de calcul : recalculer le sous-total depuis le panier réel et les prix en base, puis le vérifier à nouveau à l\'enregistrement.',
    'C\'est la règle de base de toute transaction : le client propose, le serveur dispose. Tout montant calculé côté client est une donnée d\'affichage, jamais une donnée de décision.'],
  ['AM-4', 'Sécuriser les mouvements de stock', 'P1', '2 j·h', 'BUG-003, BUG-004',
    'Vérifier puis décrémenter dans la même transaction avec verrouillage, ajouter une contrainte en base interdisant un stock négatif, restituer le stock à l\'annulation, désactiver le bouton d\'ajout pour un produit en rupture.',
    'La contrainte en base est ce qui distingue une correction d\'une garantie. La restitution à l\'annulation traite un défaut visible à la lecture du parcours : il serait incohérent de corriger le décrément sans corriger l\'incrément.'],
  ['AM-5', 'Formaliser le cycle de vie des commandes', 'P1', '1,5 j·h', 'BUG-012',
    'Déclarer explicitement les transitions autorisées, refuser les autres avec un message indiquant les possibilités, et journaliser chaque changement.',
    'Un statut n\'est pas un champ libre mais un automate : l\'expliciter rend la règle lisible et testable. Sans historique, un litige client est inarbitrable.'],
  ['AM-6', 'Fiabiliser les avis clients', 'P2', '1 j·h', 'BUG-011',
    'Conditionner le dépôt d\'un avis à une commande livrée, rattacher l\'avis à la commande et afficher la mention « Commande vérifiée ».',
    'Le modèle de données prévoit déjà le lien entre avis et commande : la correction consiste à utiliser ce qui existe, pas à l\'inventer. La mention transforme un contrôle technique en argument de confiance.'],
  ['AM-7', 'Faire de la promotion affichée la source de vérité', 'P2', '1 j·h', 'BUG-007',
    'Aligner le taux réel sur le taux annoncé après arbitrage commercial, puis générer le texte promotionnel à partir du coupon plutôt que de le saisir séparément.',
    'Corriger la valeur sans supprimer la double saisie laisserait le défaut réapparaître à la prochaine promotion. Enjeu commercial mais aussi réglementaire : l\'écart entre prix annoncé et prix pratiqué est une pratique trompeuse.'],
  ['AM-8', 'Corriger la découverte du catalogue', 'P2', '1 j·h', 'BUG-008, 009, 013',
    'Inverser la comparaison du filtre de frais de livraison, étendre la recherche à la description en ignorant accents et casse, ajouter un paramètre permettant de filtrer les restaurants fermés dans l\'API.',
    'Peu coûteux à corriger, mais situés en haut du tunnel de conversion : un client qui ne trouve pas le restaurant qu\'il cherche n\'atteint jamais le parcours d\'achat. Le filtre inversé dessert précisément le client sensible au prix.'],
  ['AM-9', 'Installer un filet de tests automatisés en intégration continue', 'P1', '3 j·h', 'Prévention',
    'Intégrer les 46 cas comme suite de non-régression exécutée à chaque modification, bloquer la livraison si un cas de règle métier échoue, ajouter un test par anomalie corrigée.',
    'C\'est la seule amélioration qui traite la cause plutôt que les symptômes. Les 16 règles manquantes n\'avaient été détectées par aucun test avant cet audit. Le coût marginal est faible : les tests sont déjà écrits et exécutables.'],
  ['AM-10', 'Corriger la suite de tests existante', 'P2', '0,5 j·h', 'Dette technique',
    'Supprimer le repli codé en dur sur un utilisateur nommé, aligner le jeu de données de test, faire échouer la construction si la suite ne passe pas à 100 %.',
    'Une suite durablement rouge cesse d\'être un signal : l\'équipe ne distingue plus une vraie régression d\'un échec connu. À traiter avant AM-9, sans quoi le filet de sécurité naîtra déjà déconsidéré.'],
];

kids.push(h2('7.1 Vue d\'ensemble'));
kids.push(tbl([1000, 3700, 900, 1000, 1600],
  ['ID', 'Amélioration', 'Priorité', 'Effort', 'Anomalies traitées'],
  AMEL.map((a) => [
    { text: a[0], mono: true, bold: true }, a[1],
    { text: a[2], mono: true, bold: a[2] === 'P0', color: a[2] === 'P0' ? FAIL : INK },
    { text: a[3], mono: true }, a[4],
  ])));

AMEL.forEach((a, i) => {
  kids.push(h2(`7.${i + 2} ${a[0]} — ${a[1]}`));
  kids.push(new Paragraph({
    children: [
      t('Priorité ', { size: 18, color: MUTED }),
      t(a[2], { size: 18, bold: true, color: a[2] === 'P0' ? FAIL : ACCENT }),
      t('   ·   Effort ', { size: 18, color: MUTED }),
      t(a[3], { size: 18, bold: true }),
      t('   ·   Traite ', { size: 18, color: MUTED }),
      t(a[4], { size: 18, bold: true }),
    ],
    spacing: { after: 110 },
  }));
  kids.push(p([t('Proposition. ', { bold: true, size: 20 }), t(a[5], { size: 20 })]));
  kids.push(p([t('Justification. ', { bold: true, size: 20 }), t(a[6], { size: 20 })]));
});

kids.push(h2('7.12 Séquencement recommandé'));
kids.push(tbl([2300, 2100, 1200, 2600], ['Lot', 'Contenu', 'Durée', 'Jalon'], [
  ['1 — Levée du No-Go', 'AM-1, AM-2, AM-3', '~7 j·h', 'Les 5 anomalies bloquantes et critiques sont corrigées'],
  ['2 — Fiabilisation', 'AM-4, AM-5, AM-10', '~4 j·h', 'Anomalies majeures corrigées, suite de tests verte'],
  ['3 — Prévention', 'AM-9', '~3 j·h', 'La non-régression est automatisée'],
  ['4 — Confiance et conversion', 'AM-6, AM-7, AM-8', '~3 j·h', 'Avis fiables, promotions cohérentes, catalogue utilisable'],
]));
kids.push(spacer(90));
kids.push(p('Revalidation après chaque lot par la même campagne. Objectif final : '
  + '46 Pass / 0 Fail.'));

kids.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================ ANNEXES
kids.push(h1('Annexes'));

kids.push(h2('A. Ce que cet audit ne couvre pas'));
kids.push(p('Quelques précisions, par honnêteté méthodologique, sur ce que cette '
  + 'campagne ne démontre pas :'));
[
  'Les tests utilisateurs (section 6) n\'ont pas été réalisés.',
  'Aucun test de performance ou de charge : rien ne peut être affirmé sur la tenue en production.',
  'Aucun audit de sécurité approfondi. À noter toutefois : aucune protection CSRF n\'a été observée sur les formulaires (connexion, panier, checkout) — vérifié, zéro occurrence dans le code.',
  'La concurrence d\'accès n\'a pas été testée : deux commandes simultanées sur le dernier article disponible pourraient aggraver BUG-004.',
  'Un seul navigateur a été utilisé ; aucune vérification mobile ni multi-navigateurs.',
].forEach((x) => kids.push(li(x)));

kids.push(h2('B. Point de sécurité relevé hors périmètre'));
kids.push(p('L\'API identifie son appelant par une clé unique et partagée, qui retombe '
  + 'en dur sur le compte alice@example.com. Concrètement, toute requête munie de la '
  + 'clé agit au nom de ce compte. Un mécanisme d\'identification par utilisateur est '
  + 'nécessaire avant toute ouverture réelle de l\'API.'));

kids.push(h2('C. Environnement testé'));
kids.push(tbl([2300, 5900], ['Élément', 'Valeur'], [
  ['Application', 'QuickOrder V3.1, déployée via Docker Compose'],
  ['URL', 'http://127.0.0.1:5000 — Swagger : /docs/'],
  ['Clé API', 'quickorder-demo-key (en-tête X-API-Key)'],
  ['Comptes de test', 'alice@example.com / Password123! — bob@example.com / Password123! — admin@quickorder.local / Admin123!'],
  ['Jeu de données', '6 restaurants (dont 1 fermé), 25 produits (dont 5 en rupture), 6 coupons (dont 1 expiré)'],
  ['Date de campagne', '22 septembre 2026'],
]));

kids.push(h2('D. Livrables du dépôt'));
kids.push(...code(
  'quality-audit-team-X/\n'
  + '├── README.md\n'
  + '├── docs/\n'
  + '│   ├── test-strategy.md       stratégie, périmètre, risques\n'
  + '│   ├── risk-matrix.md         matrice risque × impact\n'
  + '│   ├── test-cases.xlsx        les 46 cas (3 feuilles)\n'
  + '│   ├── execution-report.md    résultats et recommandation\n'
  + '│   ├── bug-reports/           13 fiches + index\n'
  + '│   ├── improvement-plan.md    10 améliorations priorisées\n'
  + '│   └── evidence/\n'
  + '│       ├── raw-log.md         journal brut des requêtes et réponses\n'
  + '│       └── results.json       résultats exploitables\n'
  + '└── tools/\n'
  + '    ├── run_campaign.py        le harnais qui exécute la campagne\n'
  + '    ├── gen_bugs.py            génère les fiches d\'anomalie\n'
  + '    ├── gen_xlsx.py            génère le classeur de cas de test\n'
  + '    └── build_docx.js          génère ce document'));
kids.push(p('Le fichier docs/user-feedback.md prévu par le brief n\'existe pas : il '
  + 'correspond à la section 6, que nous n\'avons pas réalisée.'));

// ------------------------------------------------------------------ document
const numbering = {
  config: [
    { reference: 'nogo', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.START, style: { paragraph: { indent: { left: 500, hanging: 240 } } } }] },
    ...data.bugs.map((b) => ({
      reference: `steps-${b.id}`,
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.START, style: { paragraph: { indent: { left: 500, hanging: 240 } } } }],
    })),
  ],
};

const doc = new Document({
  creator: 'Équipe QA — Audit QuickOrder',
  title: 'Audit qualité QuickOrder V3.1',
  description: 'Campagne de test, anomalies et recommandation Go/No-Go',
  numbering,
  styles: {
    default: {
      document: { run: { font: 'Calibri', size: 20, color: INK }, paragraph: { spacing: { line: 276 } } },
      heading1: { run: { font: 'Cambria', size: 34, bold: true, color: ACCENT }, paragraph: { spacing: { before: 360, after: 170 } } },
      heading2: { run: { font: 'Cambria', size: 26, bold: true, color: ACCENT }, paragraph: { spacing: { before: 260, after: 120 } } },
      heading3: { run: { font: 'Cambria', size: 22, bold: true, color: INK }, paragraph: { spacing: { before: 180, after: 90 } } },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1130, bottom: 1130, left: 1270, right: 1270 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [t('Audit qualité — QuickOrder V3.1', { size: 16, color: MUTED })],
          alignment: AlignmentType.RIGHT,
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [t('Page ', { size: 16, color: MUTED }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: MUTED }),
            t(' sur ', { size: 16, color: MUTED }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: MUTED })],
        })],
      }),
    },
    children: kids,
  }],
});

const out = path.join(ROOT, 'Audit-qualite-QuickOrder.docx');
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log('écrit : ' + out + ' (' + Math.round(buf.length / 1024) + ' Ko)');
  console.log('paragraphes/blocs : ' + kids.length);
});
