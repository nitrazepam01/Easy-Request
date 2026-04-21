create table if not exists public.profiles (
    nickname_norm text primary key,
    nickname_display text not null,
    created_at timestamptz not null default timezone('utc', now()),
    last_seen_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.question_state (
    nickname_norm text not null references public.profiles(nickname_norm) on delete cascade,
    question_id text not null,
    last_selected text,
    last_wrong_selected text,
    last_is_correct boolean,
    attempt_count integer not null default 0,
    wrong_count integer not null default 0,
    ever_wrong boolean not null default false,
    mastered boolean not null default false,
    updated_at timestamptz not null default timezone('utc', now()),
    primary key (nickname_norm, question_id)
);

create index if not exists question_state_nickname_idx
    on public.question_state (nickname_norm);

create table if not exists public.user_state (
    nickname_norm text primary key references public.profiles(nickname_norm) on delete cascade,
    current_page text not null default '首页/登录',
    current_question_id text,
    active_source text,
    active_filters jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default timezone('utc', now())
);
