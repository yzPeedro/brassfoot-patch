(() => {
  'use strict';
  const W = 900, H = 420, LEFT = 4, TOP = 4, FW = W - 8, FH = H - 8, AY = FH / FW;
  const CONTACT = .022;
  const LINE = 'rgba(235,247,236,.8)';
  const SHADOW = 'rgba(0,0,0,.35)';
  const NAME_FONT = 'bold 10px Tahoma, Verdana, "Segoe UI", sans-serif';
  const NAME_FONT_LIGHT = 'bold 9px Tahoma, Verdana, "Segoe UI", sans-serif';
  const GOAL_FONT = 'bold 13px Tahoma, Verdana, "Segoe UI", sans-serif';
  const BALL_ACCENTS = [[20, 20, 20], [20, 45, 140], [205, 25, 35], [240, 120, 20], [25, 140, 60], [120, 40, 160], [200, 160, 20], [0, 150, 200]];
  const REFEREE = {name: 'Anderson Daronco', kit: [240, 210, 20]};
  const SHAPE = [[.04, .5], [.25, .16], [.2, .39], [.2, .62], [.25, .85], [.38, .47], [.46, .65], [.54, .35], [.5, .77], [.66, .21], [.7, .52]];
  const TEAMS = [
    {fill: [12, 64, 196], ring: [255, 255, 255],
      names: ['Cássio', 'William', 'Fabrício Bruno', 'Villalba', 'Kauã Moraes', 'Lucas Romero', 'Lucas Silva', 'Matheus Pereira', 'Gerson', 'Wanderson', 'Kaio Jorge'],
      start: [[.07, .5], [.58, .14], [.44, .4], [.46, .64], [.62, .86], [.55, .44], [.63, .58], [.74, .36], [.7, .74], [.82, .2], [.84, .52]]},
    {fill: [200, 22, 34], ring: [16, 16, 16],
      names: ['Rossi', 'Varela', 'Léo Ortiz', 'Léo Pereira', 'Alex Sandro', 'Pulgar', 'Jorginho', 'Paquetá', 'Carrascal', 'Samuel Lino', 'Pedro'],
      start: [[.955, .49], [.86, .3], [.885, .45], [.88, .6], [.85, .8], [.785, .49], [.76, .64], [.66, .3], [.62, .66], [.52, .2], [.5, .5]]}
  ];

  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const rand = (a, b) => a + Math.random() * (b - a);
  const rgba = (c, a) => 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')';
  const dist = (ax, ay, bx, by) => Math.hypot(ax - bx, (ay - by) * AY);

  function seeded(seed) {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function noiseGrid(seed, columns, rows) {
    const next = seeded(seed);
    const values = new Float64Array(columns * rows);
    for (let i = 0; i < values.length; i++) values[i] = next();
    return values;
  }

  function sample(grid, columns, rows, x, y) {
    const gx = x * (columns - 1), gy = y * (rows - 1);
    const x0 = Math.floor(gx), y0 = Math.floor(gy);
    const x1 = Math.min(columns - 1, x0 + 1), y1 = Math.min(rows - 1, y0 + 1);
    let tx = gx - x0, ty = gy - y0;
    tx = tx * tx * (3 - 2 * tx);
    ty = ty * ty * (3 - 2 * ty);
    const a = grid[y0 * columns + x0], b = grid[y0 * columns + x1];
    const c = grid[y1 * columns + x0], d = grid[y1 * columns + x1];
    return (a + (b - a) * tx) + ((c + (d - c) * tx) - (a + (b - a) * tx)) * ty;
  }

  function wearZone(x, y) {
    let zone = 0;
    for (const goal of [.045, .955]) {
      const dx = (x - goal) / .07, dy = (y - .5) / .16;
      zone = Math.max(zone, Math.exp(-(dx * dx + dy * dy)));
      const sx = (x - (goal < .5 ? .11 : .89)) / .03, sy = (y - .5) / .05;
      zone = Math.max(zone, .8 * Math.exp(-(sx * sx + sy * sy)));
    }
    const cx = (x - .5) / .07, cy = (y - .5) / .18;
    zone = Math.max(zone, .7 * Math.exp(-(cx * cx + cy * cy)));
    return Math.max(zone, Math.exp(-Math.pow((y - .5) / .22, 2)) * .35);
  }

  const textures = new Map();
  function pitchTexture(condition) {
    if (textures.has(condition)) return textures.get(condition);
    const lightGreen = [[38, 146, 64], [44, 134, 60], [72, 124, 56], [90, 116, 58]];
    const darkGreen = [[30, 126, 55], [37, 118, 53], [63, 112, 51], [80, 105, 53]];
    const dry = [150, 146, 82], dirt = [124, 96, 64];
    const wearAmount = [0, .3, .7, 1.15], dryAmount = [0, .05, .35, .55], grain = [5, 6, 9, 12];
    const seed = 2026 * 31 + condition;
    const coarse = noiseGrid(seed, 13, 9), fine = noiseGrid(seed + 7, 41, 25);
    const speck = seeded(seed + 11);
    const bands = condition === 0 ? 14 : 12;
    const canvas = document.createElement('canvas');
    canvas.width = FW;
    canvas.height = FH;
    const context = canvas.getContext('2d');
    const image = context.createImageData(FW, FH);
    const data = image.data;
    for (let y = 0; y < FH; y++) {
      const ny = y / FH;
      for (let x = 0; x < FW; x++) {
        const nx = x / FW;
        const base = (Math.floor(nx * bands) & 1) === 0 ? lightGreen[condition] : darkGreen[condition];
        const smooth = sample(coarse, 13, 9, nx, ny);
        const detail = sample(fine, 41, 25, nx, ny);
        const wear = clamp(wearZone(nx, ny) * wearAmount[condition] * (.55 + smooth * .9) - (1 - detail) * .25, 0, 1);
        const dryness = clamp(dryAmount[condition] * (smooth * 1.2 - .2), 0, 1);
        const jitter = (speck() - .5) * grain[condition] + (detail - .5) * grain[condition];
        let r = base[0] + (dry[0] - base[0]) * dryness;
        let g = base[1] + (dry[1] - base[1]) * dryness;
        let b = base[2] + (dry[2] - base[2]) * dryness;
        r += (dirt[0] - r) * wear;
        g += (dirt[1] - g) * wear;
        b += (dirt[2] - b) * wear;
        const i = (y * FW + x) * 4;
        data[i] = clamp(r + jitter, 0, 255);
        data[i + 1] = clamp(g + jitter, 0, 255);
        data[i + 2] = clamp(b + jitter * .6, 0, 255);
        data[i + 3] = 255;
      }
    }
    context.putImageData(image, 0, 0);
    textures.set(condition, canvas);
    return canvas;
  }

  function colorDistance(a, b) {
    return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  }

  function createMatch() {
    const teams = TEAMS.map((team, side) => team.names.map((name, i) => ({
      side, i, name, x: team.start[i][0], y: team.start[i][1], vx: 0, vy: 0, tx: team.start[i][0], ty: team.start[i][1],
      phase: Math.random() * Math.PI * 2, rate: rand(.25, .55), runUntil: 0, runX: 0, runY: 0, immuneUntil: 0
    })));
    const accents = BALL_ACCENTS.map(color => ({color, score: Math.min(...TEAMS.map(team => colorDistance(color, team.fill)))}))
      .filter(item => item.score > 140);
    const ball = {x: .752, y: .385, vx: 0, vy: 0, lift: 0, spin: 0, alpha: 1,
      style: Math.floor(Math.random() * 12), accent: accents.length ? accents[Math.floor(Math.random() * accents.length)].color : BALL_ACCENTS[0]};
    return {
      teams, ball, time: 0, mode: 'carry', owner: teams[0][7], heading: [1, 0], holdSince: -1, nextDecision: .9,
      flight: null, intended: null, tackleTry: new Map(), referee: {x: .66, y: .52, vx: 0, vy: 0, tx: .66, ty: .52, ax: .752, ay: .385},
      phase: 'play', phaseAt: 0, kickoffSide: 0, goalText: '', goalUntil: 0, keeperHoldUntil: 0, fadeOut: 0, restartSpot: null
    };
  }

  const uOf = (side, x) => side === 0 ? x : 1 - x;
  const xOf = (side, u) => side === 0 ? u : 1 - u;
  const all = match => match.teams[0].concat(match.teams[1]);

  function nearest(list, x, y, skip) {
    let best = null, bestD = Infinity;
    for (const player of list) {
      if (player === skip) continue;
      const d = dist(player.x, player.y, x, y);
      if (d < bestD) { bestD = d; best = player; }
    }
    return {player: best, d: bestD};
  }

  function ballU(match, side) { return uOf(side, match.ball.x); }

  function shapeTarget(match, player, attacking, kickoff) {
    const [baseU, baseY] = SHAPE[player.i];
    const ball = match.ball;
    if (kickoff) {
      let u = Math.min(baseU * .62 + .02, .43);
      let y = baseY;
      if (match.kickoffSide === player.side && player.i === 10) { u = .497; y = .5; }
      if (match.kickoffSide === player.side && player.i === 7) { u = .47; y = .56; }
      return [xOf(player.side, u), y];
    }
    const bu = ballU(match, player.side);
    if (player.i === 0) {
      const u = .025 + clamp(bu, 0, 1) * .05;
      return [xOf(player.side, u), .5 + (ball.y - .5) * .32];
    }
    const shift = (bu - .45) * .5 + (attacking ? .07 : -.03);
    let u = baseU + shift + (attacking ? (baseU - .2) * .12 : 0);
    u = clamp(u, .08, attacking ? .9 : .78);
    const spread = attacking ? 1.04 : .8;
    let y = .5 + (baseY - .5) * spread + (ball.y - .5) * (player.i >= 5 ? .28 : .2);
    const t = match.time * player.rate + player.phase;
    u += Math.sin(t) * .012;
    y += Math.cos(t * 1.3) * .018;
    return [xOf(player.side, u), clamp(y, .05, .95)];
  }

  function steer(player, dt, speed) {
    const dx = player.tx - player.x, dy = (player.ty - player.y) * AY;
    const d = Math.hypot(dx, dy);
    let wantX = 0, wantY = 0;
    if (d > .002) {
      const s = Math.min(speed, d * 2.4);
      wantX = dx / d * s;
      wantY = dy / d * s;
    }
    const k = Math.min(1, dt * 5);
    player.vx += (wantX - player.vx) * k;
    player.vy += (wantY - player.vy) * k;
    player.x += player.vx * dt;
    player.y += player.vy * dt / AY;
  }

  function launch(match, from, toX, toY, kind, receiver, lift) {
    const ball = match.ball;
    const x1 = clamp(toX, kind === 'shot' ? -.02 : .02, kind === 'shot' ? 1.02 : .98);
    const y1 = clamp(toY, .03, .97);
    const d = dist(ball.x, ball.y, x1, y1);
    const dur = kind === 'shot' ? rand(.45, .62) : .3 + d * (lift > .3 ? 2.1 : 1.7);
    match.flight = {x0: ball.x, y0: ball.y, x1, y1, start: match.time, dur, lift, kind, from, receiver, outcome: null, checked: new Set()};
    match.mode = 'flight';
    match.owner = null;
    match.intended = receiver;
    from.immuneUntil = match.time + .5;
  }

  function choosePass(match, owner, pressured) {
    const side = owner.side, mates = match.teams[side], rivals = match.teams[1 - side];
    const ownU = uOf(side, owner.x);
    let best = null, bestScore = -Infinity;
    for (const mate of mates) {
      if (mate === owner) continue;
      if (mate.i === 0 && !pressured) continue;
      const du = uOf(side, mate.x) - ownU;
      const d = dist(owner.x, owner.y, mate.x, mate.y);
      if (d < .05) continue;
      let open = Infinity, lane = Infinity;
      for (const rival of rivals) {
        open = Math.min(open, dist(rival.x, rival.y, mate.x, mate.y));
        const ax = mate.x - owner.x, ay = (mate.y - owner.y) * AY;
        const bx = rival.x - owner.x, by = (rival.y - owner.y) * AY;
        const t = clamp((ax * bx + ay * by) / (ax * ax + ay * ay || 1), 0, 1);
        lane = Math.min(lane, Math.hypot(bx - ax * t, by - ay * t));
      }
      let score = du * 2.2 + Math.min(open, .12) * 6 + Math.min(lane, .08) * 5 - Math.max(0, d - .3) * 3 + Math.random() * .5;
      if (pressured && du < 0) score += .3;
      if (mate.i === 0) score -= .8;
      if (score > bestScore) { bestScore = score; best = mate; }
    }
    return best;
  }

  function passTo(match, owner, mate, longBall) {
    const side = owner.side;
    let tx = mate.x + mate.vx * .5 + (side === 0 ? .02 : -.02);
    let ty = mate.y + mate.vy * .5 / AY;
    if (Math.random() < .09) { tx += rand(-.08, .08); ty += rand(-.12, .12); }
    const d = dist(owner.x, owner.y, tx, ty);
    launch(match, owner, tx, ty, 'pass', mate, longBall || d > .32 ? rand(.6, 1) : 0);
  }

  function shoot(match, owner) {
    const side = owner.side, dir = side === 0 ? 1 : -1, goalX = side === 0 ? 1 : 0;
    const keeper = match.teams[1 - side][0];
    const roll = Math.random();
    let outcome, tx, ty;
    if (roll < .24) {
      outcome = 'goal';
      ty = Math.random() < .5 ? rand(.415, .46) : rand(.54, .585);
      tx = goalX + dir * .006;
    } else if (roll < .62) {
      outcome = 'save';
      ty = clamp(keeper.y + rand(-.05, .05), .42, .58);
      tx = goalX - dir * .018;
    } else {
      outcome = 'wide';
      ty = Math.random() < .5 ? rand(.3, .38) : rand(.62, .7);
      tx = goalX + dir * .02;
    }
    launch(match, owner, tx, ty, 'shot', null, rand(.1, .6));
    match.flight.outcome = outcome;
    match.flight.shooter = owner;
  }

  function cross(match, owner) {
    const side = owner.side;
    const mates = match.teams[side].filter(mate => mate !== owner && mate.i >= 6);
    let target = null, bestScore = -Infinity;
    for (const mate of mates) {
      const score = uOf(side, mate.x) - Math.abs(mate.y - .5) + Math.random() * .2;
      if (score > bestScore) { bestScore = score; target = mate; }
    }
    if (!target) return false;
    const spotX = xOf(side, rand(.86, .91)), spotY = rand(.4, .6);
    target.runUntil = match.time + 2.2;
    target.runX = spotX;
    target.runY = spotY;
    launch(match, owner, spotX, spotY, 'pass', target, rand(.8, 1.1));
    return true;
  }

  function gainBall(match, player) {
    match.mode = 'carry';
    match.owner = player;
    match.intended = null;
    match.flight = null;
    match.holdSince = match.time;
    match.nextDecision = match.time + rand(.4, .95);
    match.heading = [player.side === 0 ? 1 : -1, 0];
    const ball = match.ball;
    ball.vx = 0;
    ball.vy = 0;
    if (player.i === 0 && match.phase === 'play') {
      match.keeperHoldUntil = match.time + rand(.9, 1.4);
      player.immuneUntil = match.keeperHoldUntil + .3;
    }
  }

  function decide(match) {
    const owner = match.owner, side = owner.side;
    const u = uOf(side, owner.x);
    const central = Math.abs(owner.y - .5) < .22;
    const rival = nearest(match.teams[1 - side], owner.x, owner.y);
    const pressured = rival.d < .05;
    if (owner.i === 0) {
      if (match.time < match.keeperHoldUntil) return;
      const mates = match.teams[side];
      if (Math.random() < .55) passTo(match, owner, mates[[1, 2, 3, 4][Math.floor(Math.random() * 4)]], false);
      else passTo(match, owner, mates[[7, 9, 10][Math.floor(Math.random() * 3)]], true);
      return;
    }
    if (u < .2 && pressured) {
      const mates = match.teams[side];
      passTo(match, owner, mates[[9, 10, 7][Math.floor(Math.random() * 3)]], true);
      return;
    }
    if (u > .79 && central && Math.random() < .62) { shoot(match, owner); return; }
    if (u > .77 && !central && Math.random() < .58 && cross(match, owner)) return;
    const passChance = pressured ? .72 : u > .6 ? .5 : .62;
    if (Math.random() < passChance) {
      const mate = choosePass(match, owner, pressured);
      if (mate) { passTo(match, owner, mate, false); return; }
    }
    const drift = rival.player && rival.d < .12 ? Math.sign(owner.y - rival.player.y || 1) * rand(.03, .08) : rand(-.06, .06);
    owner.runUntil = match.time + rand(.7, 1.3);
    owner.runX = clamp(owner.x + (side === 0 ? 1 : -1) * rand(.06, .12), .03, .97);
    owner.runY = clamp(owner.y + drift, .06, .94);
    if (pressured) owner.immuneUntil = match.time + .5;
    match.nextDecision = owner.runUntil;
  }

  function startKickoff(match, side) {
    match.phase = 'reset';
    match.phaseAt = match.time;
    match.kickoffSide = side;
    match.mode = 'dead';
    match.owner = null;
    match.flight = null;
    match.intended = null;
    for (const player of all(match)) player.runUntil = 0;
  }

  function finishShot(match) {
    const flight = match.flight, ball = match.ball, side = flight.from.side;
    const keeper = match.teams[1 - side][0];
    if (flight.outcome === 'goal') {
      match.phase = 'goal';
      match.phaseAt = match.time;
      match.mode = 'dead';
      match.flight = null;
      match.goalText = 'GOL · ' + flight.shooter.name;
      match.scorer = flight.shooter;
      match.goalUntil = match.time + 2.6;
      match.kickoffSide = 1 - side;
      ball.lift = 0;
      return;
    }
    if (flight.outcome === 'save' && dist(keeper.x, keeper.y, ball.x, ball.y) < CONTACT * 2.4) {
      ball.x = keeper.x + (side === 0 ? -.008 : .008);
      ball.y = keeper.y;
      gainBall(match, keeper);
      return;
    }
    if (flight.outcome === 'wide') {
      match.phase = 'goalkick';
      match.phaseAt = match.time;
      match.mode = 'return';
      match.flight = null;
      match.restartSpot = {x: xOf(1 - side, .055), y: ball.y < .5 ? .42 : .58, fromX: ball.x, fromY: ball.y, side: 1 - side};
      return;
    }
    match.mode = 'loose';
    match.flight = null;
    ball.vx = (side === 0 ? -1 : 1) * rand(.12, .2);
    ball.vy = rand(-.25, .25);
    ball.x = clamp(ball.x, .01, .99);
  }

  function updateFlight(match) {
    const flight = match.flight, ball = match.ball;
    const k = clamp((match.time - flight.start) / flight.dur, 0, 1);
    const e = 1 - Math.pow(1 - k, 1.6);
    ball.x = flight.x0 + (flight.x1 - flight.x0) * e;
    ball.y = flight.y0 + (flight.y1 - flight.y0) * e;
    ball.lift = Math.sin(Math.PI * k) * flight.lift;
    if (flight.kind === 'pass' && ball.lift < .35 && k > .12) {
      for (const rival of match.teams[1 - flight.from.side]) {
        if (flight.checked.has(rival) || dist(rival.x, rival.y, ball.x, ball.y) > CONTACT) continue;
        flight.checked.add(rival);
        if (Math.random() < .5) { gainBall(match, rival); return; }
      }
    }
    if (k < 1) return;
    if (flight.kind === 'shot') { finishShot(match); return; }
    const dx = flight.x1 - flight.x0, dy = (flight.y1 - flight.y0) * AY;
    const d = Math.hypot(dx, dy) || 1;
    match.mode = 'loose';
    match.flight = null;
    ball.lift = 0;
    ball.vx = dx / d * .05;
    ball.vy = dy / d * .05 / AY;
  }

  function updateLoose(match, dt) {
    const ball = match.ball;
    ball.x += ball.vx * dt;
    ball.y += ball.vy * dt;
    const friction = Math.exp(-1.9 * dt);
    ball.vx *= friction;
    ball.vy *= friction;
    if (ball.y < .015 || ball.y > .985) { ball.vy *= -.35; ball.y = clamp(ball.y, .015, .985); }
    if (ball.x < .008 || ball.x > .992) { ball.vx *= -.35; ball.x = clamp(ball.x, .008, .992); }
    let best = null, bestD = CONTACT;
    for (const player of all(match)) {
      if (player === match.lastLoser && match.time < match.lostUntil) continue;
      const d = dist(player.x, player.y, ball.x, ball.y);
      if (d < bestD) { bestD = d; best = player; }
    }
    if (best) gainBall(match, best);
  }

  function updateCarry(match, dt) {
    const owner = match.owner, ball = match.ball;
    const speed = Math.hypot(owner.vx, owner.vy);
    if (speed > .01) {
      const k = Math.min(1, dt * 6);
      match.heading[0] += (owner.vx / speed - match.heading[0]) * k;
      match.heading[1] += (owner.vy / speed - match.heading[1]) * k;
      const n = Math.hypot(match.heading[0], match.heading[1]) || 1;
      match.heading[0] /= n;
      match.heading[1] /= n;
    }
    const bx = owner.x + match.heading[0] * .013;
    const by = owner.y + match.heading[1] * .013 / AY;
    const k = Math.min(1, dt * 16);
    ball.x += (bx - ball.x) * k;
    ball.y += (by - ball.y) * k;
    ball.lift = 0;
    if (match.phase !== 'play') return;
    if (owner.immuneUntil < match.time) {
      for (const rival of match.teams[1 - owner.side]) {
        if (dist(rival.x, rival.y, ball.x, ball.y) > CONTACT * 1.15) continue;
        if ((match.tackleTry.get(rival) || 0) > match.time) continue;
        match.tackleTry.set(rival, match.time + 1.2);
        if (Math.random() < .5) {
          const ang = Math.atan2(rival.vy, rival.vx) + rand(-1, 1);
          match.mode = 'loose';
          match.owner = null;
          ball.vx = Math.cos(ang) * rand(.08, .16);
          ball.vy = Math.sin(ang) * rand(.08, .16) / AY;
          match.lastLoser = owner;
          match.lostUntil = match.time + .35;
          return;
        }
        owner.immuneUntil = match.time + .8;
        break;
      }
    }
    if (match.time >= match.nextDecision && match.time - match.holdSince > .35) decide(match);
  }

  function updateReturn(match, dt) {
    const spot = match.restartSpot, ball = match.ball;
    const k = clamp((match.time - match.phaseAt - .5) / 1.3, 0, 1);
    const e = k * k * (3 - 2 * k);
    ball.x = spot.fromX + (spot.x - spot.fromX) * e;
    ball.y = spot.fromY + (spot.y - spot.fromY) * e;
    ball.lift = 0;
    const keeper = match.teams[spot.side][0];
    if (k >= 1 && dist(keeper.x, keeper.y, ball.x, ball.y) < CONTACT * 1.2) {
      match.phase = 'play';
      gainBall(match, keeper);
      match.keeperHoldUntil = match.time + .7;
    }
  }

  function assignTargets(match) {
    const ball = match.ball;
    const possession = match.owner ? match.owner.side : match.flight ? match.flight.from.side : -1;
    const kickoff = match.phase === 'reset';
    const chasers = new Set();
    if (match.mode === 'loose') {
      for (const side of [0, 1]) {
        const px = ball.x + ball.vx * .35, py = ball.y + ball.vy * .35;
        const near = nearest(match.teams[side], px, py);
        if (near.player) chasers.add(near.player);
      }
      if (match.intended) chasers.add(match.intended);
    }
    let presser = null, cover = null;
    if (match.mode === 'carry' && match.owner && match.phase === 'play') {
      const rivals = match.teams[1 - match.owner.side].filter(player => player.i !== 0 || uOf(player.side, ball.x) < .16);
      const first = nearest(rivals, match.owner.x, match.owner.y);
      presser = first.player;
      cover = nearest(rivals, match.owner.x, match.owner.y, presser).player;
    }
    for (const player of all(match)) {
      const attacking = possession === player.side;
      let [tx, ty] = shapeTarget(match, player, attacking, kickoff);
      let speed = dist(player.x, player.y, tx, ty) > .08 ? .085 : .05;
      if (player.i === 0) speed = .06;
      if (kickoff) speed = .1;
      if (match.phase === 'goal') {
        const shooter = match.scorer;
        if (shooter && player.side === shooter.side && player !== shooter && player.i !== 0 && dist(player.x, player.y, shooter.x, shooter.y) < .3) {
          tx = shooter.x + Math.cos(player.phase) * .03;
          ty = shooter.y + Math.sin(player.phase) * .05;
          speed = .09;
        } else {
          tx = player.x;
          ty = player.y;
        }
      } else if (!kickoff) {
        if (player.runUntil > match.time) { tx = player.runX; ty = player.runY; speed = .095; }
        if (match.owner === player) {
          speed = .068;
          if (player.runUntil <= match.time) {
            tx = player.x + (player.side === 0 ? .03 : -.03);
            ty = player.y + (.5 - player.y) * .02;
          }
          if (player.i === 0) { tx = player.x; ty = player.y; }
        } else if (match.mode === 'flight' && match.flight && match.flight.receiver === player) {
          tx = match.flight.x1;
          ty = match.flight.y1;
          speed = .1;
        } else if (match.mode === 'flight' && match.flight && match.flight.kind === 'shot' && player.i === 0 && player.side !== match.flight.from.side) {
          tx = match.flight.x1;
          ty = match.flight.y1;
          speed = .13;
        } else if (chasers.has(player)) {
          tx = ball.x + ball.vx * .3;
          ty = ball.y + ball.vy * .3;
          speed = .11;
        } else if (player === presser) {
          tx = match.owner.x + (player.side === 0 ? -.012 : .012);
          ty = match.owner.y;
          speed = .1;
        } else if (player === cover) {
          tx = (match.owner.x + xOf(player.side, .05)) / 2;
          ty = (match.owner.y + .5) / 2;
          speed = .08;
        } else if (match.mode === 'return' && match.restartSpot && player.i === 0 && player.side === match.restartSpot.side) {
          tx = match.restartSpot.x;
          ty = match.restartSpot.y;
          speed = .07;
        }
      }
      player.tx = clamp(tx, .01, .99);
      player.ty = clamp(ty, .02, .98);
      player.speed = speed;
    }
    if (match.mode === 'carry' && match.owner && match.phase === 'play' && Math.random() < .006) {
      const side = match.owner.side;
      const runner = match.teams[side][[7, 9, 10, 6, 8][Math.floor(Math.random() * 5)]];
      if (runner !== match.owner && runner.runUntil < match.time) {
        runner.runUntil = match.time + rand(1.4, 2.4);
        runner.runX = clamp(runner.x + (side === 0 ? 1 : -1) * rand(.1, .18), .05, .95);
        runner.runY = clamp(runner.y + rand(-.12, .12), .08, .92);
      }
    }
    const anchored = player => player === match.owner || player === presser || chasers.has(player) || (match.flight && match.flight.receiver === player);
    for (const team of match.teams) {
      for (let a = 1; a < team.length; a++) {
        for (let b = a + 1; b < team.length; b++) {
          const p = team[a], q = team[b];
          const d = dist(p.tx, p.ty, q.tx, q.ty);
          if (d > .05 || d === 0) continue;
          const push = (.05 - d) / 2;
          const nx = (p.tx - q.tx) / d, ny = (p.ty - q.ty) * AY / d;
          if (!anchored(p)) { p.tx += nx * push; p.ty += ny * push / AY; }
          if (!anchored(q)) { q.tx -= nx * push; q.ty -= ny * push / AY; }
        }
      }
    }
  }

  function updateReferee(match, dt) {
    const ref = match.referee, ball = match.ball;
    if (dist(ball.x, ball.y, ref.ax, ref.ay) > .08 || match.phase === 'reset') {
      ref.ax = ball.x;
      ref.ay = ball.y;
      const possession = match.owner ? match.owner.side : match.flight ? match.flight.from.side : 0;
      const dir = possession === 0 ? 1 : -1;
      ref.tx = match.phase === 'reset' ? .5 + .07 : clamp(ball.x - dir * .1, .06, .94);
      ref.ty = match.phase === 'reset' ? .66 : clamp(ball.y + (ball.y < .5 ? .13 : -.13), .06, .94);
    }
    let tx = ref.tx, ty = ref.ty;
    for (const player of all(match)) {
      const d = dist(player.x, player.y, tx, ty);
      if (d < .04 && d > 0) {
        tx += (tx - player.x) / d * (.04 - d);
        ty += (ty - player.y) / d * (.04 - d);
      }
    }
    const temp = {x: ref.x, y: ref.y, vx: ref.vx, vy: ref.vy, tx, ty};
    steer(temp, dt, .075);
    Object.assign(ref, {x: temp.x, y: temp.y, vx: temp.vx, vy: temp.vy});
  }

  function step(match, dt) {
    match.time += dt;
    const ball = match.ball;
    const before = [ball.x, ball.y];
    assignTargets(match);
    for (const player of all(match)) steer(player, dt, player.speed);
    if (match.phase === 'goal') {
      if (match.time - match.phaseAt > 1.9) { startKickoff(match, match.kickoffSide); match.fadeOut = match.time; }
    } else if (match.phase === 'reset') {
      const fade = match.time - match.fadeOut;
      if (fade < .35) ball.alpha = 1 - fade / .35;
      else {
        ball.x = .5;
        ball.y = .5;
        ball.lift = 0;
        ball.alpha = Math.min(1, (fade - .35) / .35);
      }
      const ready = all(match).every(player => dist(player.x, player.y, player.tx, player.ty) < .03);
      if (fade > 1 && (ready || match.time - match.phaseAt > 7)) {
        ball.alpha = 1;
        match.phase = 'play';
        const taker = match.teams[match.kickoffSide][10];
        taker.x = clamp(taker.x, .45, .55);
        gainBall(match, taker);
        match.nextDecision = match.time + .5;
        match.holdSince = match.time - 1;
        match.kickoffPass = true;
      }
    } else if (match.mode === 'return') {
      updateReturn(match, dt);
    }
    if (match.mode === 'carry' && match.kickoffPass && match.time >= match.nextDecision) {
      match.kickoffPass = false;
      passTo(match, match.owner, match.teams[match.owner.side][7], false);
    } else if (match.mode === 'carry') updateCarry(match, dt);
    else if (match.mode === 'flight') updateFlight(match);
    else if (match.mode === 'loose') updateLoose(match, dt);
    ball.spin += Math.hypot(ball.x - before[0], (ball.y - before[1]) * AY) * 110;
    updateReferee(match, dt);
  }

  function px(x) { return LEFT + x * FW; }
  function py(y) { return TOP + y * FH; }

  function circle(ctx, x, y, r) {
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
  }

  function ellipseArc(ctx, cx, cy, rx, ry, start, extent, pie) {
    ctx.beginPath();
    if (pie) ctx.moveTo(cx, cy);
    ctx.ellipse(cx, cy, rx, ry, 0, -start * Math.PI / 180, -(start + extent) * Math.PI / 180, extent > 0);
    if (pie) ctx.closePath();
  }

  function polygon(ctx, points) {
    ctx.beginPath();
    points.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.closePath();
    ctx.fill();
  }

  function pentagon(cx, cy, size) {
    return Array.from({length: 5}, (_, k) => {
      const a = -Math.PI / 2 + k * Math.PI * 2 / 5;
      return [cx + Math.cos(a) * size, cy + Math.sin(a) * size];
    });
  }

  function star(cx, cy, size) {
    return Array.from({length: 10}, (_, k) => {
      const a = -Math.PI / 2 + k * Math.PI / 5;
      const r = k % 2 === 0 ? size : size * .45;
      return [cx + Math.cos(a) * r, cy + Math.sin(a) * r];
    });
  }

  function drawBall(ctx, ball, cx, cy, r) {
    ctx.save();
    ctx.globalAlpha = ball.alpha;
    ctx.fillStyle = '#fff';
    circle(ctx, cx, cy, r);
    ctx.fill();
    ctx.save();
    circle(ctx, cx, cy, r);
    ctx.clip();
    ctx.translate(cx, cy);
    ctx.rotate(ball.spin);
    const mark = rgba(ball.accent, 1);
    ctx.fillStyle = mark;
    ctx.strokeStyle = mark;
    switch (ball.style) {
      case 0:
        polygon(ctx, pentagon(0, 0, r * .4));
        for (let k = 0; k < 5; k++) {
          const a = k * Math.PI * 2 / 5;
          polygon(ctx, pentagon(Math.cos(a) * r * 1.05, Math.sin(a) * r * 1.05, r * .36));
        }
        break;
      case 1:
      case 2:
        for (let k = 0; k < 3; k++) {
          ctx.save();
          ctx.rotate(k * Math.PI * 2 / 3);
          ellipseArc(ctx, r / 6 + r / 2, 0, r / 2, r / 2, 90, 180, true);
          ctx.fill();
          if (ball.style === 2) ctx.fillRect(r / 2, -1, r / 2, 2);
          ctx.restore();
        }
        break;
      case 3:
        for (let k = 0; k < 4; k++) {
          const a = k * Math.PI / 2;
          polygon(ctx, [[Math.cos(a) * r * .25, Math.sin(a) * r * .25], [Math.cos(a + .35) * r * .95, Math.sin(a + .35) * r * .95], [Math.cos(a - .35) * r * .95, Math.sin(a - .35) * r * .95]]);
        }
        break;
      case 4:
        ctx.lineWidth = Math.max(1, r * .18);
        circle(ctx, 0, 0, r / 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(-r, 0); ctx.lineTo(-r / 2, 0);
        ctx.moveTo(r / 2, 0); ctx.lineTo(r, 0);
        ctx.stroke();
        break;
      case 5:
        ctx.lineWidth = Math.max(1, r * .2);
        ellipseArc(ctx, 0, 0, r, r, 30, 70); ctx.stroke();
        ellipseArc(ctx, 0, 0, r, r, 210, 70); ctx.stroke();
        ellipseArc(ctx, 0, 0, r / 2, r / 2, 120, 60); ctx.stroke();
        break;
      case 6:
        ctx.lineWidth = Math.max(1.2, r * .26);
        ellipseArc(ctx, 0, r * 2 / 3, r, r, 30, 120); ctx.stroke();
        ellipseArc(ctx, 0, -r * 2 / 3, r, r, 210, 120); ctx.stroke();
        break;
      case 7:
        for (let k = 0; k < 4; k++) {
          const a = k * Math.PI / 2 + .4;
          ctx.fillRect(Math.cos(a) * r * .55 - r / 5, Math.sin(a) * r * .55 - 1, r * 2 / 5, 3);
        }
        break;
      case 8:
        for (let k = 0; k < 6; k++) {
          const a = k * Math.PI / 3;
          circle(ctx, Math.cos(a) * r * .62 + .5, Math.sin(a) * r * .62 + .5, 1.5);
          ctx.fill();
        }
        circle(ctx, 0, 0, 2);
        ctx.fill();
        break;
      case 9:
        for (let k = 0; k < 3; k++) {
          const a = k * Math.PI * 2 / 3;
          polygon(ctx, star(Math.cos(a) * r * .55, Math.sin(a) * r * .55, r * .35));
        }
        break;
      case 10:
        ctx.lineWidth = Math.max(1, r * .18);
        ctx.beginPath();
        ctx.moveTo(-r, -r / 3); ctx.lineTo(r, -r / 3);
        ctx.moveTo(-r, r / 3); ctx.lineTo(r, r / 3);
        ctx.stroke();
        break;
      default:
        ellipseArc(ctx, 0, 0, r, r, 20, 50, true); ctx.fill();
        ellipseArc(ctx, 0, 0, r, r, 200, 50, true); ctx.fill();
    }
    ctx.restore();
    ctx.strokeStyle = 'rgba(0,0,0,.67)';
    ctx.lineWidth = 1;
    circle(ctx, cx, cy, r);
    ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,.55)';
    const hw = Math.max(2, r / 2), hh = Math.max(2, r / 3);
    ctx.beginPath();
    ctx.ellipse(cx - r / 2 + hw / 2, cy - r * 3 / 4 + hh / 2, hw / 2, hh / 2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawPenaltyArea(ctx, rightSide) {
    const largeW = Math.max(80, FW / 7), largeH = FH / 2;
    const smallW = Math.max(32, FW / 22), smallH = FH / 4;
    const y1 = TOP + (FH - largeH) / 2, y2 = TOP + (FH - smallH) / 2;
    const x1 = rightSide ? LEFT + FW - largeW : LEFT;
    const x2 = rightSide ? LEFT + FW - smallW : LEFT;
    ctx.strokeRect(x1, y1, largeW, largeH);
    ctx.strokeRect(x2, y2, smallW, smallH);
    ctx.strokeRect(rightSide ? LEFT + FW : LEFT - 8, TOP + FH / 2 - FH / 10, 8, FH / 5);
  }

  function inFocus(match, player) {
    if (match.owner === player) return true;
    if (match.flight && match.flight.receiver === player) return true;
    return dist(player.x, player.y, match.ball.x, match.ball.y) < .1;
  }

  function drawPlayers(ctx, match) {
    for (const team of match.teams) {
      const kit = TEAMS[team[0].side];
      for (const player of team) {
        const x = px(player.x), y = py(player.y);
        ctx.fillStyle = SHADOW;
        circle(ctx, x + 1, y + 3, 10);
        ctx.fill();
        ctx.fillStyle = rgba(kit.fill, 1);
        circle(ctx, x, y, 10);
        ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,.27)';
        ctx.beginPath();
        ctx.ellipse(x - 2.5, y - 5, 4.5, 3, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = rgba(kit.ring, 1);
        ctx.lineWidth = 2;
        circle(ctx, x, y, 10);
        ctx.stroke();
      }
    }
    for (const team of match.teams) {
      for (const player of team) {
        const x = px(player.x), y = py(player.y);
        const focus = inFocus(match, player);
        ctx.font = focus ? NAME_FONT : NAME_FONT_LIGHT;
        const width = ctx.measureText(player.name).width;
        const tx = x - width / 2, ty = y - 13;
        if (focus) {
          ctx.fillStyle = 'rgba(0,0,0,.35)';
          ctx.beginPath();
          if (ctx.roundRect) ctx.roundRect(tx - 4, ty - 10, width + 8, 13, 5); else ctx.rect(tx - 4, ty - 10, width + 8, 13);
          ctx.fill();
          ctx.fillStyle = '#fff';
        } else {
          ctx.fillStyle = 'rgba(0,0,0,.47)';
          ctx.fillText(player.name, tx + 1, ty + 1);
          ctx.fillStyle = 'rgba(255,255,255,.75)';
        }
        ctx.fillText(player.name, tx, ty);
      }
    }
  }

  function draw(ctx, match, condition) {
    ctx.drawImage(pitchTexture(condition), LEFT, TOP, FW, FH);
    ctx.strokeStyle = LINE;
    ctx.fillStyle = LINE;
    ctx.lineWidth = 2;
    ctx.strokeRect(LEFT + 2, TOP + 2, FW - 4, FH - 4);
    const mid = LEFT + FW / 2;
    ctx.beginPath();
    ctx.moveTo(mid, TOP + 2);
    ctx.lineTo(mid, TOP + FH - 2);
    ctx.stroke();
    const diameter = Math.min(96, FH / 3);
    circle(ctx, mid, TOP + FH / 2, diameter / 2);
    ctx.stroke();
    circle(ctx, mid, TOP + FH / 2, 3);
    ctx.fill();
    drawPenaltyArea(ctx, false);
    drawPenaltyArea(ctx, true);
    drawPlayers(ctx, match);
    const ref = match.referee, kit = REFEREE.kit;
    const rx = px(ref.x), ry = py(ref.y);
    ctx.fillStyle = SHADOW;
    circle(ctx, rx + 1, ry + 3, 8);
    ctx.fill();
    ctx.fillStyle = rgba(kit, 1);
    circle(ctx, rx, ry, 8);
    ctx.fill();
    ctx.strokeStyle = kit[0] + kit[1] + kit[2] < 200 ? '#fff' : 'rgb(20,20,20)';
    ctx.lineWidth = 2;
    circle(ctx, rx, ry, 8);
    ctx.stroke();
    ctx.font = NAME_FONT_LIGHT;
    const refW = ctx.measureText(REFEREE.name).width;
    ctx.fillStyle = 'rgba(0,0,0,.31)';
    ctx.fillText(REFEREE.name, rx - refW / 2 + 1, ry - 11);
    ctx.fillStyle = 'rgba(255,236,140,.67)';
    ctx.fillText(REFEREE.name, rx - refW / 2, ry - 12);
    const ball = match.ball;
    const bx = px(ball.x), by = py(ball.y);
    const radius = 7 + Math.round(ball.lift * 3);
    const offset = 2 + Math.round(ball.lift * 7);
    ctx.save();
    ctx.globalAlpha = ball.alpha;
    ctx.fillStyle = SHADOW;
    circle(ctx, bx + .5 + offset / 2, by + 2.5 + offset, 5.5);
    ctx.fill();
    ctx.restore();
    drawBall(ctx, ball, bx, by - Math.round(ball.lift * 5), radius);
    if (match.goalText && match.time < match.goalUntil) {
      const fade = Math.min(1, (match.goalUntil - match.time) / .4, (match.time - match.goalUntil + 2.6) / .25);
      ctx.save();
      ctx.globalAlpha = clamp(fade, 0, 1);
      ctx.font = GOAL_FONT;
      const width = ctx.measureText(match.goalText).width;
      ctx.fillStyle = 'rgba(11,22,51,.82)';
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(W / 2 - width / 2 - 14, 18, width + 28, 28, 14); else ctx.rect(W / 2 - width / 2 - 14, 18, width + 28, 28);
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.fillText(match.goalText, W / 2 - width / 2, 37);
      ctx.restore();
    }
  }

  function mount(canvas, options = {}) {
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    let condition = clamp(Number(options.condition) || 0, 0, 3);
    let match = createMatch();
    let userPaused = !!options.paused;
    let visible = true;
    let frame = 0, last = 0, ready = false, destroyed = false;
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(1, Math.round(rect.width * ratio));
      const height = Math.max(1, Math.round(rect.width * H / W * ratio));
      if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
      ctx.setTransform(width / W, 0, 0, height / H, 0, 0);
      render();
    };
    const render = () => {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = '#155b30';
      ctx.fillRect(0, 0, W, H);
      draw(ctx, match, condition);
      if (!ready) { ready = true; options.onReady?.(); }
    };
    const running = () => !userPaused && visible && !document.hidden && !destroyed;
    const loop = now => {
      frame = 0;
      if (!running()) return;
      const dt = last ? Math.min(.05, (now - last) / 1000) : 0;
      last = now;
      if (dt > 0) step(match, dt);
      render();
      frame = requestAnimationFrame(loop);
    };
    const wake = () => {
      if (frame || !running()) return;
      last = 0;
      frame = requestAnimationFrame(loop);
    };
    const observer = typeof ResizeObserver === 'function' ? new ResizeObserver(resize) : null;
    observer?.observe(canvas);
    if (!observer) window.addEventListener('resize', resize);
    const viewport = typeof IntersectionObserver === 'function' ? new IntersectionObserver(entries => {
      visible = entries.some(entry => entry.isIntersecting);
      wake();
    }) : null;
    viewport?.observe(canvas);
    const onVisibility = () => wake();
    document.addEventListener('visibilitychange', onVisibility);
    resize();
    wake();
    return {
      setCondition(value) {
        const next = clamp(Number(value) || 0, 0, 3);
        if (next === condition) return;
        condition = next;
        render();
      },
      play() { userPaused = false; wake(); },
      pause() { userPaused = true; },
      restart() { match = createMatch(); render(); wake(); },
      get playing() { return running(); },
      destroy() {
        destroyed = true;
        if (frame) cancelAnimationFrame(frame);
        observer?.disconnect();
        viewport?.disconnect();
        if (!observer) window.removeEventListener('resize', resize);
        document.removeEventListener('visibilitychange', onVisibility);
      }
    };
  }

  window.LivePitch = {mount};
})();
