/* MyKwizz : page d'accueil publique (#/bienvenue), vue avant la connexion.
   Mouvements repris de la technique de kresco.ma (sans son nom, son logo ni sa mascotte) :
   - le logo du hero glisse et rapetisse jusqu'à la barre du haut quand on défile ;
   - la phrase du hero change de verbe ; ses lettres se resserrent puis reprennent leur place ;
   - des croquis de quizz (coche, minuterie, podium…) se dessinent autour ;
   - chaque étape du parcours se dévoile au défilement et joue sa petite démo en boucle. */
"use strict";

/* Logo MyKwizz : le « K » et son triangle « lecture », redessinés en SVG à partir de Logo_Kwizz_and_Co.png.
   Le K prend la couleur du texte (bleu nuit, ou clair en mode sombre), le triangle reste violet. */
const LOGO_K = '<svg class="logo-mark" viewBox="428 318 432 410" aria-hidden="true" focusable="false"><path fill="currentColor" d="M535 331V716q0 6-6 6h-51q-43 0-43-43V410q0-37 32-53l60-30q8-4 8 4Z"/><path fill="currentColor" d="M535 505L667 375q4-4 10-4h99q11 0 3 8L541 612q-6 6-6-3Z"/><path fill="currentColor" d="M574 607l54-51q4-3 7 0l150 156q8 10-3 10h-98q-11 0-19-9l-91-96q-3-4 0-10Z"/><path class="logo-play" d="M722 474q0-16 14-8l108 62q14 8 0 16l-108 62q-14 8-14-8Z"/></svg>';
function logoKwizz() { return LOGO_K + '<span class="logo-mot"><span class="logo-my">My</span>Kwizz</span>'; }

const VERBES = ["Révise", "Apprends", "Progresse", "Retiens"];
let nettoyages = [];
function auNettoyage(f) { nettoyages.push(f); }
function nettoyerVue() { nettoyages.forEach(f => f()); nettoyages = []; }
const calme = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/* Chaque lettre devient un <span> avec un décalage propre (--gx, --gy, --gr). */
function lettres(mot, depart, total) {
  return [...mot].map((l, i) => {
    const pos = total > 1 ? ((depart + i) / (total - 1)) * 2 - 1 : 0;   // -1 à gauche, 1 à droite
    const gy = (Math.sin((depart + i) * 2.3) * 0.6).toFixed(2);
    const gr = (pos * 0.9 + Math.cos((depart + i) * 1.7) * 0.4).toFixed(2);
    return `<span class="vt-glyphe" style="--gx:${pos.toFixed(2)};--gy:${gy};--gr:${gr}">${l === " " ? "&nbsp;" : h(l)}</span>`;
  }).join("");
}

function vueBienvenue() {
  const suffixe = "en jouant.";
  contenu.innerHTML = `
  <div class="vitrine">
    <header class="vt-barre" id="vt-barre">
      <a class="vt-logo" id="vt-logo" href="#/bienvenue" aria-label="MyKwizz, haut de page">${logoKwizz()}</a>
      <nav class="vt-liens" aria-label="Sections de la page">
        <button type="button" data-cible="vt-parcours">Comment ça marche</button>
        <button type="button" data-cible="vt-createurs">Créer un quizz</button>
        <button type="button" data-cible="vt-faq">Questions</button>
      </nav>
      <a class="bouton vt-barre-cta" href="#/connexion">Se connecter</a>
    </header>

    <section class="vt-hero" aria-labelledby="vt-titre">
      <div class="vt-place-logo" id="vt-place-logo" aria-hidden="true"></div>
      <h1 class="vt-phrase" id="vt-titre">
        <span class="vh">Révise en jouant avec MyKwizz.</span>
        <span class="vt-ligne" id="vt-ligne" aria-hidden="true">
          <span class="vt-prefixe" id="vt-prefixe">${lettres(VERBES[0], 0, VERBES[0].length + suffixe.length + 1)}</span>
          <span class="vt-suffixe">${lettres(suffixe, VERBES[0].length + 1, VERBES[0].length + suffixe.length + 1)}<i class="vt-surligne"></i></span>
        </span>
        <span class="vt-regle" aria-hidden="true"><span>0</span><span>100 %</span></span>
        <span class="vt-croquis" aria-hidden="true">
          <svg class="cq cq-coche" viewBox="0 0 64 64"><circle cx="32" cy="32" r="26"/><path d="M20 33l8 8 16-18"/></svg>
          <svg class="cq cq-chrono" viewBox="0 0 64 64"><circle class="fond" cx="32" cy="34" r="22"/><circle class="arc" cx="32" cy="34" r="22" pathLength="100"/><path d="M27 8h10M32 8v5M32 34V22"/></svg>
          <svg class="cq cq-podium" viewBox="0 0 80 56"><rect x="4" y="22" width="22" height="30" rx="4"/><rect x="29" y="8" width="22" height="44" rx="4"/><rect x="54" y="30" width="22" height="22" rx="4"/></svg>
          <span class="cq cq-choix"><b>A</b><b class="on">B</b><b>C</b><b>D</b></span>
          <svg class="cq cq-question" viewBox="0 0 60 72"><rect x="4" y="4" width="52" height="64" rx="10"/><path d="M22 26a8 8 0 1 1 11 7.4c-2 .9-3 2.4-3 4.6v3M30 50v.5"/></svg>
          <i class="cq cq-anneau"></i>
        </span>
      </h1>
      <div class="vt-hero-actions">
        <a class="vt-pilule" href="#/inscription">C'est parti<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg></a>
        <a class="vt-lien" href="#/connexion">J'ai déjà un compte</a>
      </div>
    </section>

    <section class="vt-bande">
      <p>Des quizz courts.<br><em>Le corrigé tout de suite.</em></p>
    </section>

    <section class="vt-parcours" id="vt-parcours" aria-labelledby="vt-parcours-titre">
      <h2 class="vt-titre-section" id="vt-parcours-titre">Ta partie, étape par étape.</h2>
      <p class="vt-chapeau">Choisir, jouer, comprendre, se comparer : tout s'enchaîne sans quitter la page.</p>

      ${etape(1, "Choisis", "Un quizz court, sur le sujet que tu révises.", `
        <div class="dm dm-choisir">
          ${[["jaune", "Capitales d'Europe", "1:00"], ["rose", "Gestion de projet", "2:00"], ["vert", "Les bases de Python", "libre"]].map(([c, t, d], i) => `
          <div class="dm-paquet ${c}" style="--i:${i}"><span class="dm-entete"><b>10</b> questions<em>${d}</em></span><span class="dm-titre">${t}</span></div>`).join("")}
          <i class="dm-curseur"></i>
        </div>`)}

      ${etape(2, "Joue", "Une question à la fois, une minuterie si le quizz en a une.", `
        <div class="dm dm-jouer">
          <div class="dm-haut"><span class="dm-barres"><i></i><i></i><i></i><i></i><i></i></span><span class="dm-chrono">0:42</span></div>
          <p class="dm-question">Quelle est la capitale de la Pologne ?</p>
          <div class="dm-choix">${["Cracovie", "Varsovie", "Gdańsk", "Poznań"].map((c, i) => `<span class="${i === 1 ? "bon" : ""}"><i></i>${c}</span>`).join("")}</div>
          <i class="dm-curseur"></i>
        </div>`)}

      ${etape(3, "Comprends", "Le score, puis le corrigé de chaque question : juste, faux ou oublié.", `
        <div class="dm dm-corrige">
          <p class="dm-score"><span>8</span><small>/10</small></p>
          <ul>
            <li class="j"><svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6"/></svg>Varsovie</li>
            <li class="f"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg><s>Cracovie</s></li>
            <li class="o"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7.5"/></svg>Lisbonne</li>
          </ul>
        </div>`)}

      ${etape(4, "Compare", "Chaque quizz a son classement. Rejoue pour grimper.", `
        <div class="dm dm-podium">
          ${[["noa", "7", 2], ["toi", "10", 1], ["eli", "6", 3]].map(([n, s, r]) => `
          <div class="dm-marche r${r}"><span class="dm-nom">${n}</span><span class="dm-pts">${s}</span><i>${r}</i></div>`).join("")}
        </div>`)}

      ${etape(5, "Crée", "Écris un quizz, importe un fichier .txt ou .json, ou demande un brouillon à l'IA.", `
        <div class="dm dm-ia" id="vt-createurs">
          <p class="dm-invite"><span>10 questions sur les bases de Python</span><i class="dm-caret"></i></p>
          <p class="dm-pense"><i></i><i></i><i></i></p>
          <ol>
            <li>Que renvoie <code>len("kwizz")</code> ?</li>
            <li>Quel type a <code>[1, 2, 3]</code> ?</li>
            <li>Comment définir une fonction ?</li>
          </ol>
          <p class="dm-relis">Tu relis avant de publier.</p>
        </div>`)}
    </section>

    <section class="vt-faq" id="vt-faq" aria-labelledby="vt-faq-titre">
      <h2 class="vt-titre-section" id="vt-faq-titre">Avant de commencer.</h2>
      <div class="vt-questions">
        ${[
          ["Faut-il un compte ?", "Oui : un login et un mot de passe suffisent. Il sert à garder ton historique, tes meilleurs scores et ta place au classement."],
          ["Comment le score est-il calculé ?", "Une question est juste si tu coches toutes ses bonnes réponses, et seulement elles. Il n'y a pas de demi-point."],
          ["Il y a toujours une minuterie ?", "Non. Chaque quizz choisit : sans limite, ou un temps total. À zéro, tes réponses sont envoyées telles quelles."],
          ["L'IA est-elle obligatoire ?", "Non. Kwizz marche sans IA et sans Internet. Si elle est activée, elle propose des brouillons de quizz (toujours relus par un humain) et explique tes erreurs."],
          ["Puis-je importer mes propres questions ?", "Oui, depuis l'administration : un fichier .txt avec # TITRE:, Q:, + et -, ou un fichier .json."],
        ].map(([q, r]) => `<details class="vt-q"><summary>${q}<i aria-hidden="true"></i></summary><p>${r}</p></details>`).join("")}
      </div>
    </section>

    <section class="vt-fin">
      <p class="vt-fin-titre">Une question.<br><em>Puis la suivante.</em></p>
      <a class="bouton vt-fin-cta" href="#/inscription">Créer mon compte<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg></a>
      <p class="vt-pied">MyKwizz · projet PROJ531, Polytech, 2026</p>
    </section>
  </div>`;

  brancherLogo();
  brancherPhrase();
  brancherApparitions();
  contenu.querySelectorAll(".vt-liens button").forEach(b => b.addEventListener("click", () =>
    document.getElementById(b.dataset.cible)?.scrollIntoView({ behavior: calme() ? "auto" : "smooth", block: "start" })));
}

function etape(n, titre, texte, demo) {
  return `<article class="vt-etape" style="--n:${n}">
    <h3>${titre}</h3><p>${texte}</p><span class="vt-num">Étape ${String(n).padStart(2, "0")}</span>
    <div class="vt-carte"><span class="vt-badge" aria-hidden="true">${n}</span><div aria-hidden="true">${demo}</div></div>
  </article>`;
}

/* Le logo de la barre part de la place du grand logo et rejoint la barre au fil du défilement. */
function brancherLogo() {
  const logo = $("#vt-logo"), place = $("#vt-place-logo"), barre = $("#vt-barre");
  let depart = null;
  const mesurer = () => {
    logo.style.transform = "none";
    const l = logo.getBoundingClientRect(), p = place.getBoundingClientRect();
    depart = {
      dx: p.left + p.width / 2 - (l.left + l.width / 2),
      dy: p.top + scrollY + p.height / 2 - (l.top + l.height / 2),
      s: p.width / l.width,
      course: Math.max(160, p.top + scrollY + p.height / 2 - (l.top + l.height / 2)),
    };
    peindre();
  };
  const peindre = () => {
    if (!depart) return;
    const t = Math.min(1, Math.max(0, scrollY / depart.course));
    const e = 1 - Math.pow(1 - t, 3);                    // sortie douce
    const r = 1 - e;
    logo.style.transform = `translate(${depart.dx * r}px, ${(depart.dy - scrollY) * r + 0}px) scale(${1 + (depart.s - 1) * r})`;
    barre.style.setProperty("--p", t.toFixed(3));
  };
  let image = 0;
  const auDefilement = () => { cancelAnimationFrame(image); image = requestAnimationFrame(peindre); };
  addEventListener("scroll", auDefilement, { passive: true });
  addEventListener("resize", mesurer);
  auNettoyage(() => { removeEventListener("scroll", auDefilement); removeEventListener("resize", mesurer); });
  document.fonts?.ready.then(mesurer);
  mesurer();
}

/* Change le verbe toutes les 3 s : les lettres arrivent resserrées et penchées, puis se placent. */
function brancherPhrase() {
  const ligne = $("#vt-ligne"), prefixe = $("#vt-prefixe");
  const suffixe = "en jouant.";
  let i = 0;
  const jouer = () => {
    if (calme()) return;
    ligne.style.transition = "none";
    ligne.style.setProperty("--ecart", "-0.85");
    ligne.classList.add("arrive");
    void ligne.offsetWidth;
    ligne.style.transition = "";
    ligne.style.setProperty("--ecart", "0");
    ligne.classList.remove("arrive");
  };
  const suivant = () => {
    if (document.hidden || scrollY > innerHeight) return;
    i = (i + 1) % VERBES.length;
    const v = VERBES[i];
    prefixe.innerHTML = lettres(v, 0, v.length + suffixe.length + 1);
    ligne.querySelectorAll(".vt-suffixe .vt-glyphe").forEach((g, k) => {
      const pos = ((v.length + 1 + k) / (v.length + suffixe.length)) * 2 - 1;
      g.style.setProperty("--gx", pos.toFixed(2));
    });
    jouer();
  };
  requestAnimationFrame(jouer);
  const minuteur = setInterval(suivant, 3000);
  auNettoyage(() => clearInterval(minuteur));
}

/* Les étapes se dévoilent en entrant dans l'écran ; leur démo ne tourne que quand elles sont visibles. */
function brancherApparitions() {
  const io = new IntersectionObserver(entrees => entrees.forEach(e => {
    e.target.classList.toggle("en-vue", e.isIntersecting);
    if (e.isIntersecting) e.target.classList.add("vu");
  }), { threshold: 0.25 });
  contenu.querySelectorAll(".vt-etape, .vt-bande, .vt-faq, .vt-fin").forEach(el => io.observe(el));
  auNettoyage(() => io.disconnect());
}
