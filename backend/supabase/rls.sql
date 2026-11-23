alter table public.users enable row level security;
alter table public.events enable row level security;
alter table public.registrations enable row level security;

revoke all on table public.users from anon, authenticated;
revoke all on table public.events from anon, authenticated;
revoke all on table public.registrations from anon, authenticated;

grant select on table public.users to service_role;
grant select on table public.events to service_role;
grant select, insert on table public.registrations to service_role;
