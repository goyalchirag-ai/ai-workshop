const main = document.querySelector('#main');
const dialog = document.querySelector('#profile-dialog');
let userId = '';
try { userId = sessionStorage.getItem('gather.userId') || ''; } catch { /* Storage may be unavailable. */ }
let renderVersion = 0;
let activeRequest;
let toastTimer;
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initials = title => String(title || 'Event').split(/\s+/).slice(0,2).map(s => s[0]).join('').toUpperCase();
const capacity = event => event.capacity == null ? 'No limit' : Number(event.capacity).toLocaleString();
const status = event => String(event.status || 'Unspecified');
const badge = event => `<span class="badge ${status(event).toLowerCase() === 'open' ? 'open' : 'closed'}">${escape(status(event))}</span>`;
const eventLink = id => `#/events/${encodeURIComponent(id)}`;
const date = value => value && !Number.isNaN(Date.parse(value)) ? new Intl.DateTimeFormat(undefined,{dateStyle:'medium'}).format(new Date(value)) : 'Date unavailable';
const title = text => { document.title = `${text} · Gather`; };

async function api(path, options = {}) {
  const {signal = activeRequest?.signal, ...rest} = options;
  let response;
  try { response = await fetch(`/api${path}`, {signal, ...rest, headers:{'Accept':'application/json', ...(rest.body ? {'Content-Type':'application/json'} : {}), ...rest.headers}}); }
  catch(error) { if(error.name === 'AbortError') throw error; throw new Error('Unable to reach the server. Check your connection and try again.'); }
  let body;
  try { body = await response.json(); } catch { throw new Error('The server returned an unexpected response. Please try again.'); }
  if(!response.ok) { const error = new Error(body.error || 'Something went wrong. Please try again.'); error.status = response.status; throw error; }
  if(!Object.hasOwn(body,'data')) throw new Error('The server response is missing its data.');
  return body.data;
}
function empty(heading, message, action = '<a class="button primary" href="#/events">Browse events</a>') {
  return `<section class="empty"><div class="empty-symbol" aria-hidden="true">◎</div><h2>${escape(heading)}</h2><p>${escape(message)}</p>${action}</section>`;
}
function hero(label, heading, description, art = false) {
  return `<section class="hero"><div><span class="eyebrow">${label}</span><h1>${heading}</h1><p>${description}</p></div>${art ? '<div class="hero-art" aria-hidden="true"><div class="mini-pass"><span class="eyebrow">Gather / together</span><strong>Be part of it.</strong><span class="muted small">Good people. Great moments.</span></div></div>' : ''}</section>`;
}
function showProfile() { document.querySelector('#user-id').value = userId; document.querySelector('#profile-error').textContent = ''; dialog.showModal(); }
function updateProfile() { document.querySelector('#profile-label').textContent = userId ? `User ${userId.slice(0,8)}` : 'Set user ID'; }
function toast(message) { const el = document.querySelector('#toast'); el.textContent = message; el.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => el.hidden = true, 5000); }
document.querySelector('#profile-button').addEventListener('click',showProfile);
document.querySelector('#close-profile').addEventListener('click',() => dialog.close());
document.querySelector('#profile-form').addEventListener('submit', event => {
  event.preventDefault();
  const value = document.querySelector('#user-id').value.trim();
  if(!uuid.test(value)) { document.querySelector('#profile-error').textContent = 'Enter a valid user UUID, including all four hyphens.'; return; }
  userId = value.toLowerCase();
  try { sessionStorage.setItem('gather.userId', userId); } catch { /* Continue with in-memory identity. */ }
  updateProfile(); dialog.close(); toast('Registration profile saved.'); render();
});

async function eventsPage(version) {
  title('Discover events');
  const events = await api('/events');
  if(version !== renderVersion) return;
  main.innerHTML = hero('Find your people', 'Your next great<br>gathering starts here.', 'Discover events, make connections, and save your place in something worth showing up for.',true) +
    `<div class="section-heading"><h2>Explore events <span class="badge">${events.length}</span></h2><span class="muted small">A place for every curious mind</span></div>
    <div class="toolbar"><label class="sr-only" for="event-search">Search events</label><input class="search" type="search" id="event-search" placeholder="Search events by name…"><div class="filters"><label class="sr-only" for="event-status">Event status</label><select id="event-status"><option value="">All statuses</option>${[...new Set(events.map(status))].sort().map(s=>`<option value="${escape(s)}">${escape(s)}</option>`).join('')}</select><button class="button ghost" id="refresh">Refresh</button></div></div><div id="event-results" aria-live="polite"></div>`;
  const draw = () => {
    const query = document.querySelector('#event-search').value.toLowerCase();
    const filter = document.querySelector('#event-status').value;
    const visible = events.filter(e => String(e.title || '').toLowerCase().includes(query) && (!filter || status(e) === filter));
    document.querySelector('#event-results').innerHTML = visible.length ? `<div class="grid">${visible.map(e => `<article class="event-card"><div class="event-art" aria-hidden="true"><span class="monogram">${escape(initials(e.title))}</span><span class="orb"></span></div><div class="card-body"><div>${badge(e)}</div><h3><a href="${eventLink(e.id)}">${escape(e.title || 'Untitled event')}</a></h3><div class="card-bottom"><span class="muted">${capacity(e)}${e.capacity == null ? '' : ' capacity'}</span><a class="button" href="${eventLink(e.id)}">View event</a></div></div></article>`).join('')}</div>` : empty(events.length ? 'No matching events' : 'More gatherings are on the way',events.length ? 'Try another name or status to find your gathering.' : 'Events will appear here when they are added.', '<button class="button" id="reset-search">Reset filters</button>');
    document.querySelector('#reset-search')?.addEventListener('click',() => { document.querySelector('#event-search').value = ''; document.querySelector('#event-status').value = ''; draw(); });
  };
  document.querySelector('#event-search').addEventListener('input',draw);
  document.querySelector('#event-status').addEventListener('change',draw);
  document.querySelector('#refresh').addEventListener('click',render);
  draw();
}

async function detailsPage(id, version) {
  const event = await api(`/events/${encodeURIComponent(id)}`);
  if(version !== renderVersion) return;
  title(event.title || 'Event details');
  main.innerHTML = `<a class="back" href="#/events">All events</a><div class="split"><article class="detail-ticket"><div class="detail-body">${badge(event)}<h1>${escape(event.title || 'Untitled event')}</h1><p>Make room for a new connection.<br>Reserve your place and keep your registration in one place.</p><dl class="metadata"><div><dt>Organizer ID</dt><dd>${escape(event.organizer_id || 'Not provided')}</dd></div><div><dt>Event ID</dt><dd>${escape(event.id)}</dd></div></dl></div><div class="detail-stub"><span class="capacity">${capacity(event)}</span><p class="eyebrow">${event.capacity == null ? 'Capacity' : 'Total capacity'}</p></div></article>
    <aside class="panel"><h2>Save your seat</h2><div class="inset"><span class="eyebrow">Registration profile</span><p>${userId ? `User <strong>${escape(userId.slice(0,8))}</strong><br><button class="button ghost" id="change-user">Change user</button>` : 'Choose your user ID to reserve a place at this event.'}</p></div><p>One registration per person. Your confirmation will appear under My registrations.</p><button class="button primary" id="register">${userId ? 'Register for this event' : 'Set user ID to register'}</button><div id="registration-result" aria-live="polite"></div><p class="small muted">Availability is confirmed when you register.</p></aside></div><section class="cta"><div><span class="eyebrow">All together, in one place</span><h2>Your next experience is waiting.</h2><p>Find your saved registrations whenever you need them.</p></div><a class="button" href="#/registrations">My registrations</a></section>`;
  document.querySelector('#change-user')?.addEventListener('click',showProfile);
  document.querySelector('#register').addEventListener('click',async () => {
    if(!userId) { showProfile(); return; }
    const button = document.querySelector('#register');
    const result = document.querySelector('#registration-result');
    button.disabled = true; button.textContent = 'Reserving your place…'; result.innerHTML = '';
    try {
      // Do not abort a write when navigation changes; the server may already have committed it.
      await api('/registrations',{method:'POST',body:JSON.stringify({user_id:userId,event_id:id}),signal:null});
      if(version !== renderVersion) return;
      button.textContent = 'You’re registered';
      result.innerHTML = '<div class="notice success"><strong>Your place is confirmed.</strong><br><a href="#/registrations">View your registration</a></div>';
      toast('You’re on the list. See you there!');
    } catch(error) {
      if(version !== renderVersion) return;
      button.disabled = false; button.textContent = 'Register for this event';
      result.innerHTML = `<div class="notice error-text" role="alert">${escape(error.message)}${error.status === 409 ? '<br><a href="#/registrations">View my registrations</a>' : ''}</div>`;
    }
  });
}

async function registrationsPage(version) {
  title('My registrations');
  if(!userId) { main.innerHTML = hero('Your collection','Your registrations','Good moments start with a place on the list.') + empty('Your gatherings, all together','Set your existing user ID to find the events you’ve registered for.','<button id="choose-user" class="button primary">Set user ID</button>'); document.querySelector('#choose-user').addEventListener('click',showProfile); return; }
  const registrations = await api(`/me/registrations?user_id=${encodeURIComponent(userId)}`);
  if(version !== renderVersion) return;
  registrations.sort((a,b)=>(Date.parse(b.created_at)||0)-(Date.parse(a.created_at)||0));
  main.innerHTML = hero(`${registrations.length} registered gatherings`,'Your registrations','Your events, newest registrations first. All in one place.') +
    (registrations.length ? `<div class="ticket-list">${registrations.map(r=>{const e = r.events || {};return `<article class="ticket"><div class="ticket-main"><div class="initials" aria-hidden="true">${escape(initials(e.title))}</div><div>${badge(e)}<h2>${escape(e.title || 'Event unavailable')}</h2><p class="small muted">${capacity(e)}${e.capacity == null ? '' : ' total capacity'}</p></div><a class="button" href="${eventLink(r.event_id)}">View event</a></div><div class="ticket-stub"><span class="badge">Registered</span><time>${escape(date(r.created_at))}</time><span class="success small">Registration confirmed</span><span class="small muted">${escape(r.id)}</span></div></article>`;}).join('')}</div>` : empty('Your first gathering awaits','Explore the events and register for something that catches your curiosity.')) +
    '<section class="cta"><div><span class="eyebrow">Discover more</span><h2>Looking for something new?</h2><p>Good conversations start with showing up.</p></div><a class="button primary" href="#/events">Browse events</a></section>';
}

async function organizerPage(version) {
  title('Organizer dashboard');
  const events = await api('/events');
  if(version !== renderVersion) return;
  main.innerHTML = hero('Host terminal','Organizer dashboard','A clear view of your gatherings. Explore events and see who’s on the list.') +
    `<div class="toolbar"><div class="filters"><label class="sr-only" for="organizer-scope">Events shown</label><select id="organizer-scope"><option value="all">All events</option><option value="mine" ${userId ? '' : 'disabled'}>My hosted events</option></select></div><button class="button ghost" id="refresh">Refresh</button></div><div id="organizer-results"></div>`;
  const draw = () => {
    const visible = document.querySelector('#organizer-scope').value === 'mine' ? events.filter(e=>String(e.organizer_id).toLowerCase() === userId) : events;
    const limited = visible.filter(e=>e.capacity != null);
    document.querySelector('#organizer-results').innerHTML = `<section class="metrics"><div class="metric"><span class="eyebrow">Events in view</span><div class="metric-value">${visible.length}</div></div><div class="metric"><span class="eyebrow">Open events</span><div class="metric-value success">${visible.filter(e=>status(e).toLowerCase()==='open').length}</div></div><div class="metric"><span class="eyebrow">Limited-capacity seats</span><div class="metric-value">${limited.reduce((sum,e)=>sum+Number(e.capacity),0).toLocaleString()}</div></div></section><div class="section-heading"><h2>Events overview</h2><span class="muted small">Select an event to view attendees</span></div>` + (visible.length ? visible.map(e=>`<article class="organizer-row"><div class="initials" aria-hidden="true">${escape(initials(e.title))}</div><div class="row-title">${badge(e)}<h3>${escape(e.title || 'Untitled event')}</h3><span class="small muted">${capacity(e)}${e.capacity == null ? '' : ' total capacity'}</span></div><a class="button primary" href="#/organizer/${encodeURIComponent(e.id)}">View attendees</a><a class="button" href="${eventLink(e.id)}">Event details</a></article>`).join('') : empty('No events here yet','Events matching this organizer will appear here when they are added.'));
  };
  document.querySelector('#organizer-scope').addEventListener('change',draw);
  document.querySelector('#refresh').addEventListener('click',render);
  draw();
}

function csvCell(value) {
  let text = String(value ?? '');
  if(/^[\s]*[=+\-@\t\r\n]/.test(text)) text = "'" + text;
  return `"${text.replace(/"/g,'""')}"`;
}
async function attendeesPage(id,version) {
  const [event,attendees] = await Promise.all([api(`/events/${encodeURIComponent(id)}`),api(`/events/${encodeURIComponent(id)}/registrations`)]);
  if(version !== renderVersion) return;
  title('Event attendees');
  attendees.sort((a,b)=>(Date.parse(b.created_at)||0)-(Date.parse(a.created_at)||0));
  main.innerHTML = `<a class="back" href="#/organizer">Organizer dashboard</a>` + hero('Guest list',escape(event.title || 'Event attendees'),'Every connection starts with a name on the list.') +
    `<section class="metrics"><div class="metric"><span class="eyebrow">Registrations</span><div class="metric-value">${attendees.length}</div></div><div class="metric"><span class="eyebrow">Total capacity</span><div class="metric-value">${capacity(event)}</div></div><div class="metric"><span class="eyebrow">Remaining places</span><div class="metric-value success">${event.capacity == null ? 'No limit' : Math.max(0,event.capacity-attendees.length).toLocaleString()}</div></div></section><div class="toolbar"><label class="sr-only" for="attendee-search">Search attendee email or ID</label><input class="search" id="attendee-search" type="search" placeholder="Search email or user ID…"><div class="filters"><button class="button ghost" id="refresh">Refresh</button><button class="button" id="export" ${attendees.length ? '' : 'disabled'}>Export CSV</button></div></div><div id="attendee-results" aria-live="polite"></div>`;
  const draw = () => {
    const search = document.querySelector('#attendee-search').value.toLowerCase();
    const visible = attendees.filter(r=>`${r.users?.email || ''} ${r.user_id}`.toLowerCase().includes(search));
    document.querySelector('#attendee-results').innerHTML = visible.length ? `<div class="table-wrap"><table><caption class="sr-only">Registered attendees</caption><thead><tr><th scope="col">Attendee</th><th scope="col">Role</th><th scope="col">Registered on</th><th scope="col">Registration ID</th></tr></thead><tbody>${visible.map(r=>`<tr><td>${escape(r.users?.email || r.user_id)}</td><td>${escape(r.users?.role || 'Not provided')}</td><td>${escape(date(r.created_at))}</td><td>${escape(r.id)}</td></tr>`).join('')}</tbody></table></div>` : empty(attendees.length ? 'No matching attendees' : 'The guest list starts here',attendees.length ? 'Try a different email or user ID.' : 'New registrations will appear here. Refresh to see the latest list.','');
  };
  document.querySelector('#attendee-search').addEventListener('input',draw);
  document.querySelector('#refresh').addEventListener('click',render);
  document.querySelector('#export').addEventListener('click',()=>{
    const rows = [['Registration ID','User ID','Email','Role','Registered at'],...attendees.map(r=>[r.id,r.user_id,r.users?.email,r.users?.role,r.created_at])];
    const url = URL.createObjectURL(new Blob(['\uFEFF'+rows.map(row=>row.map(csvCell).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = `gather-attendees-${id}.csv`; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  draw();
}

async function render() {
  const version = ++renderVersion;
  activeRequest?.abort(); activeRequest = new AbortController();
  const route = location.hash.replace(/^#\/?/,'').split('/');
  const page = route[0] || 'events';
  document.querySelectorAll('[data-nav]').forEach(a=>{ if(a.dataset.nav === page) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current'); });
  main.innerHTML = '<div class="loading" role="status">Getting everything ready…</div>';
  main.setAttribute('aria-busy','true');
  try {
    if(page === 'events' && route[1]) await detailsPage(decodeURIComponent(route[1]),version);
    else if(page === 'events') await eventsPage(version);
    else if(page === 'registrations') await registrationsPage(version);
    else if(page === 'organizer' && route[1]) await attendeesPage(decodeURIComponent(route[1]),version);
    else if(page === 'organizer') await organizerPage(version);
    else { title('Page not found'); main.innerHTML = empty('This page isn’t here','Head back to events to find your next gathering.'); }
  } catch(error) {
    if(version !== renderVersion || error.name === 'AbortError') return;
    title('Unable to load');
    main.innerHTML = empty(error.status === 404 ? 'Event not found' : 'We couldn’t load this page',error.message,'<button class="button primary" id="retry">Try again</button> <a class="button ghost" href="#/events">Browse events</a>');
    document.querySelector('#retry').addEventListener('click',render);
  } finally { if(version === renderVersion) main.removeAttribute('aria-busy'); }
}
window.addEventListener('hashchange',()=>{ window.scrollTo(0,0); render(); main.focus({preventScroll:true}); });
updateProfile(); render();
