drop database culturaLLM;
create database if not exists culturaLLM;
use culturaLLM;


create table if not exists badge(
    badge_id int AUTO_INCREMENT primary key,
    path text not null
);

create table if not exists title(
    title_id int AUTO_INCREMENT primary key,
    name varchar(255) not null unique
);

create table if not exists mission(
    mission_id int AUTO_INCREMENT primary key,
    type ENUM('daily','weekly','objective'),
    kind ENUM('answer','question'),        --indica su cosa va a contare il valore (es: rispondi a 10 domande -> kind=answer , crea 10 domande sul calcio -> kind=question theme=calcio)
    theme int,
    description text not null,
    reward_coins int not null,
    reward_points int not null,
    value int not null,
    foreign key(theme) references theme(theme_id) on delete cascade on update cascade
);

create table if not exists avatar(
    avatar_id int AUTO_INCREMENT primary key,
    path text not null
);


create table if not exists badge_user(
    badge_id int not null,
    user_id int not null,
    primary key(badge_id,user_id),
    foreign key(badge_id) references badge(badge_id) on delete cascade on update cascade,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade
);

create table if not exists title_user(
    title_id int not null,
    user_id int not null,
    primary key(title_id,user_id),
    foreign key(title_id) references title(title_id) on delete cascade on update cascade,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade
);

create table if not exists avatar_user(
    avatar_id int not null,
    user_id int not null,
    active int default 0,
    primary key(avatar_id,user_id),
    foreign key(avatar_id) references avatar(avatar_id) on delete cascade on update cascade,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade
);


create table if not exists mission_user(
    mission_id int not null,
    user_id int not null,
    progress int default 0,
    completed int default 0,
    primary key(mission_id,user_id),
    foreign key(mission_id) references mission(mission_id) on delete cascade on update cascade,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade
);


create table if not exists llm(
    llm_id int AUTO_INCREMENT primary key,
    name varchar(255) not null,
    llm_points int default 0
);


create table if not exists user(
    user_id int AUTO_INCREMENT primary key,
    username varchar(255) unique not null,
    name varchar(255) not null,
    surname varchar(255) not null,
    bio text,
    password varchar(255) not null,
    user_points int default 0,
    --user_points_season int default 0,
    user_coins int default 0,
    created_at timestamp default CURRENT_TIMESTAMP
    last_login_at timestamp
);

create table if not exists lingua(
    lingua_id int AUTO_INCREMENT primary key,
    name varchar(255)
);

create table if not exists question(
    question_id int AUTO_INCREMENT primary key,
    question_text varchar(500) not null unique,
    created_by_user_id int,
    created_at timestamp default CURRENT_TIMESTAMP,
    rankings_times int default 0,
    --answers_number int default 0, si può fare con count *
    status ENUM('open','close') default 'open',
    foreign key(created_by_user_id) references user(user_id) on update cascade on delete set null
    --difficulty ENUM('hard','medium','easy'),  può valutarla un LLM?
    --target_culture varchar(50) default 'italiana' tabella lingua?
);

create table if not exists answer(
    answer_id int AUTO_INCREMENT primary key,
    answer_text text not null,
    answer_type ENUM('LLM','user'),
    created_at timestamp default CURRENT_TIMESTAMP
    --is_culturally_specific_response boolean
);

create table if not exists report_type(
    report_type_id int AUTO_INCREMENT primary key,
    type varchar(255) not null
);


create table if not exists report(
    report_id int AUTO_INCREMENT primary key,
    description varchar(500) default null,
    report_type_id int not null,
    foreign key(report_type_id) references report_type(report_type_id) on delete cascade on update cascade
);

create table if not exists report_question(
    report_id int not null,
    question_id int not null,
    primary key(report_id, question_id),
    foreign key(question_id) references question(question_id) on delete cascade on update cascade,
    foreign key(report_id) references report(report_id) on delete cascade on update cascade,
);

create table if not exists theme(
    theme_id int AUTO_INCREMENT primary key,
    name varchar(100) unique not null
);

create table if not exists question_theme(
    question_id int not null,
    theme_id int not null,
    primary key(question_id,theme_id),
    foreign key (question_id) references question(question_id) on delete cascade on update cascade,
    foreign key (theme_id) references theme(theme_id) on delete cascade on update cascade 
);

create table if not exists question_answer(
    question_id int not null,
    answer_id int not null,
    points int default 0,
    primary key(question_id,answer_id),
    foreign key(question_id) references question(question_id) on delete cascade on update cascade,
    foreign key(answer_id) references answer(answer_id) on delete cascade on update cascade
);

create table if not exists user_answer_question(
    user_id int not null,
    answer_id int not null,
    question_id int not null,
    answered_at timestamp default CURRENT_TIMESTAMP,
    primary key(user_id,question_id),
    foreign key(question_id,answer_id) references question_answer(question_id,answer_id) on delete cascade on update cascade,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade
);
