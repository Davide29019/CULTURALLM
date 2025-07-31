drop database culturaLLM;
create database if not exists culturaLLM;
use culturaLLM;


create table if not exists theme(
    theme_id int AUTO_INCREMENT primary key,
    name varchar(100) unique not null,
    of_the_week int default 0,
    theme_text text default null,
    theme_subtext text default null
);


insert into theme(name) values ("Cibo"),("Musica"),("Cinema"),("Moda"),("Calcio"),("Architettura"),("Letteratura"),("Scienza"),("Storia"),("Geografia"),("Filosofia"),("Sport");


create table if not exists avatar(
    avatar_id int AUTO_INCREMENT primary key,
    path text not null
);

insert into avatar(path) values(
    "/images/assets/avatar/default-avatar-circle.jpg"
);

create table if not exists title(
    title_id int AUTO_INCREMENT primary key,
    name varchar(255) not null unique
);

insert into title(name) values("Beginner");


create table if not exists user(
    user_id int AUTO_INCREMENT primary key,
    username varchar(255) unique not null,
    email varchar(255) unique not null,
    name varchar(255),
    surname varchar(255),
    bio text,
    current_avatar_id int default 1,
    current_title_id int default 1,
    password varchar(255) not null,
    salt text not null,
    user_points int default 0,
    custom_profile_image boolean default 0,
    /* stato, regione, citta???*/    
    /*--user_points_season int default 0,*/
    user_coins int default 0,
    created_at timestamp default CURRENT_TIMESTAMP,
    last_login_at timestamp,
    birthday text default null,
    location text default null,
    website text default null,
    email_notification int default 0,
    phone_number text default null,
    foreign key (current_avatar_id) references avatar(avatar_id) on delete set default on update set default
);


create table if not exists badge(
    badge_id int AUTO_INCREMENT primary key,
    title text not null,
    description text not null,
    tier ENUM('bronze', 'silver', 'gold'),
    path text not null
);

insert into badge(title, description, tier, path) values ("Cultural Explorer", "Asked 100+ questions", 'silver', '<div class="flex-shrink-0 h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center"><ion-icon name="earth-outline" class="text-2xl text-blue-400"></ion-icon></div>'),
("Helpful Contributor", "50+ helpful answers", 'silver', '<div class="flex-shrink-0 h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center"><ion-icon name="sparkles-outline" class="text-2xl text-green-400"></ion-icon></div>'),
("Community Leader", "Make it to the top 100", 'bronze', '<div class="flex-shrink-0 h-12 w-12 rounded-full bg-purple-500/20 flex items-center justify-center"><ion-icon name="people-outline" class="text-2xl text-purple-400"></ion-icon></div>'),
("Mission Master", "Completed 20 missions",'bronze',  '<div class="flex-shrink-0 h-12 w-12 rounded-full bg-orange-500/20 flex items-center justify-center"><ion-icon name="ribbon-outline" class="text-2xl text-orange-400"></ion-icon></div>');



create table if not exists mission(
    mission_id int AUTO_INCREMENT primary key,
    type ENUM('daily','weekly','objective'),
    kind ENUM('answer','question','ranking','llm','user', 'mission'),        /*--indica su cosa va a contare il valore (es: rispondi a 10 domande -> kind=answer , crea 10 domande sul calcio -> kind=question theme=calcio)*/
    theme int default null,
    description text not null,
    reward_coins int not null,
    reward_points int not null,
    reward_badge int default null,
    reward_title text default null,
    value int not null,
    foreign key(theme) references theme(theme_id) on delete cascade on update cascade
);


insert into mission (type, kind, description, reward_coins, reward_points, value) values ('objective', 'user', 'Modifica il profilo utente inserendo alcuni dati personali', 20, 10, 1);
INSERT INTO mission (type, kind, theme, description, reward_points, reward_coins, value) VALUES
-- DAILY - QUESTIONS (5 per tema)
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Cibo'), 'Crea 5 domande sul tema Cibo', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Musica'), 'Crea 5 domande sul tema Musica', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Cinema'), 'Crea 5 domande sul tema Cinema', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Moda'), 'Crea 5 domande sul tema Moda', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Calcio'), 'Crea 5 domande sul tema Calcio', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Architettura'), 'Crea 5 domande sul tema Architettura', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Letteratura'), 'Crea 5 domande sul tema Letteratura', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Scienza'), 'Crea 5 domande sul tema Scienza', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Storia'), 'Crea 5 domande sul tema Storia', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Geografia'), 'Crea 5 domande sul tema Geografia', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Filosofia'), 'Crea 5 domande sul tema Filosofia', 20, 15, 5),
('daily', 'question', (SELECT theme_id FROM theme WHERE name = 'Sport'), 'Crea 5 domande sul tema Sport', 20, 15, 5),

-- DAILY - ANSWERS
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Cibo'), 'Rispondi a 10 domande sul tema Cibo', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Musica'), 'Rispondi a 10 domande sul tema Musica', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Cinema'), 'Rispondi a 10 domande sul tema Cinema', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Moda'), 'Rispondi a 10 domande sul tema Moda', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Calcio'), 'Rispondi a 10 domande sul tema Calcio', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Architettura'), 'Rispondi a 10 domande sul tema Architettura', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Letteratura'), 'Rispondi a 10 domande sul tema Letteratura', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Scienza'), 'Rispondi a 10 domande sul tema Scienza', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Storia'), 'Rispondi a 10 domande sul tema Storia', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Geografia'), 'Rispondi a 10 domande sul tema Geografia', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Filosofia'), 'Rispondi a 10 domande sul tema Filosofia', 40, 25, 10),
('daily', 'answer', (SELECT theme_id FROM theme WHERE name = 'Sport'), 'Rispondi a 10 domande sul tema Sport', 40, 25, 10),

-- DAILY - LLM
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Cibo'), 'Fai generare all''LLM 10 domande sul tema Cibo', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Musica'), 'Fai generare all''LLM 10 domande sul tema Musica', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Cinema'), 'Fai generare all''LLM 10 domande sul tema Cinema', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Moda'), 'Fai generare all''LLM 10 domande sul tema Moda', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Calcio'), 'Fai generare all''LLM 10 domande sul tema Calcio', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Architettura'), 'Fai generare all''LLM 10 domande sul tema Architettura', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Letteratura'), 'Fai generare all''LLM 10 domande sul tema Letteratura', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Scienza'), 'Fai generare all''LLM 10 domande sul tema Scienza', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Storia'), 'Fai generare all''LLM 10 domande sul tema Storia', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Geografia'), 'Fai generare all''LLM 10 domande sul tema Geografia', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Filosofia'), 'Fai generare all''LLM 10 domande sul tema Filosofia', 40, 25, 10),
('daily', 'llm', (SELECT theme_id FROM theme WHERE name = 'Sport'), 'Fai generare all''LLM 10 domande sul tema Sport', 40, 25, 10),

-- WEEKLY - QUESTION
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Cibo'), 'Crea 20 domande sul tema Cibo', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Musica'), 'Crea 20 domande sul tema Musica', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Cinema'), 'Crea 20 domande sul tema Cinema', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Moda'), 'Crea 20 domande sul tema Moda', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Calcio'), 'Crea 20 domande sul tema Calcio', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Architettura'), 'Crea 20 domande sul tema Architettura', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Letteratura'), 'Crea 20 domande sul tema Letteratura', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Scienza'), 'Crea 20 domande sul tema Scienza', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Storia'), 'Crea 20 domande sul tema Storia', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Geografia'), 'Crea 20 domande sul tema Geografia', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Filosofia'), 'Crea 20 domande sul tema Filosofia', 80, 50, 20),
('weekly', 'question', (SELECT theme_id FROM theme WHERE name = 'Sport'), 'Crea 20 domande sul tema Sport', 80, 50, 20),

-- OBJECTIVE
('objective', 'question', null, 'Crea 100 domande su qualsiasi tema', 200, 100, 100),
('objective', 'answer', null, 'Rispondi a 100 domande su qualsiasi tema', 200, 100, 100),
('objective', 'ranking', null, 'Classifica 100 risposte su qualsiasi tema', 200, 100, 100),
('objective', 'llm', null, 'Fai generare all''LLM 100 domande su qualsiasi tema', 200, 100, 100),
('objective', 'question', null, 'Crea 500 domande su qualsiasi tema', 500, 250, 500),
('objective', 'answer', null, 'Rispondi a 500 domande su qualsiasi tema', 500, 250, 500),
('objective', 'ranking', null, 'Classifica 500 risposte su qualsiasi tema', 500, 250, 500),
('objective', 'llm', null, 'Fai generare all''LLM 500 domande su qualsiasi tema', 500, 250, 500),
('objective', 'question', null, 'Crea 1000 domande su qualsiasi tema', 1000, 500, 1000),
('objective', 'answer', null, 'Rispondi a 1000 domande su qualsiasi tema', 1000, 500, 1000),
('objective', 'ranking', null, 'Classifica 1000 risposte su qualsiasi tema', 1000, 500, 1000),
('objective', 'mission', null, 'Completa 100 missioni su qualsiasi tema', 200, 100, 100),
('objective', 'llm', null, 'Fai generare all''LLM 1000 domande su qualsiasi tema', 1000, 500, 1000);



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
    primary key(avatar_id,user_id),
    foreign key(avatar_id) references avatar(avatar_id) on delete cascade on update cascade,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade
);


create table if not exists mission_user(
    mission_id int not null,
    user_id int not null,
    progress int default 0,
    completed int default 0,
    started_at timestamp default CURRENT_TIMESTAMP, /*per controllare quando scadono*/
    expired int default 0,
    completed_at timestamp default null,
    primary key(mission_id,user_id),
    foreign key(mission_id) references mission(mission_id) on delete cascade on update cascade,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade
);



create table if not exists llm(
    llm_id int AUTO_INCREMENT primary key,
    name varchar(255) not null,
    llm_points int default 0
);


insert into llm (name) values ("gemma3:4b"),("gemma3:1b");



create table if not exists lingua(
    lingua_id int AUTO_INCREMENT primary key,
    name varchar(255)
);

create table if not exists question(
    question_id int AUTO_INCREMENT primary key,
    question_tags text default null,
    question_text text null,
    created_by_user_id int default null,
    created_by_llm_id int default null,
    created_at timestamp default CURRENT_TIMESTAMP,
    rankings_times int default 0,
    points_assigned int default 0,
    /*--answers_number int default 0, si può fare con count **/
    upvotes int default 0,
    status ENUM('open', 'ranking', 'close') default 'open',
    downvotes int default 0,
    foreign key(created_by_user_id) references user(user_id) on update cascade on delete set null,
    foreign key(created_by_llm_id) references llm(llm_id) on update cascade on delete set null
    /*--difficulty ENUM('hard','medium','easy'),  può valutarla un LLM?
    --target_culture varchar(50) default 'italiana' tabella lingua?*/   
);

/*
create table if not exists report_type(
    report_type_id int AUTO_INCREMENT primary key,
    type varchar(255) not null
);
*/

create table if not exists report(
    report_id int AUTO_INCREMENT primary key,
    /*description varchar(500) default null,
    report_type_id int not null,*/
    user_id int not null,
    question_id int not null,
    unique(user_id, question_id),
    /*foreign key(report_type_id) references report_type(report_type_id) on delete cascade on update cascade,*/
    foreign key(user_id) references user(user_id) on delete cascade on update cascade,
    foreign key(question_id) references question(question_id) on update cascade on delete cascade
);
/*
create table if not exists report_question(
    report_id int not null,
    question_id int not null,
    primary key(report_id, question_id),
    foreign key(question_id) references question(question_id) on delete cascade on update cascade,
    foreign key(report_id) references report(report_id) on delete cascade on update cascade
);*/


create table if not exists question_theme(
    question_id int not null,
    theme_id int not null,
    primary key(question_id,theme_id),
    foreign key (question_id) references question(question_id) on delete cascade on update cascade,
    foreign key (theme_id) references theme(theme_id) on delete cascade on update cascade 
);


create table if not exists answer(
    answer_id int AUTO_INCREMENT primary key,
    llm_id int default null,
    user_id int default null,
    question_id int not null,
    answered_at timestamp default CURRENT_TIMESTAMP,
    answer_text text not null,
    points int default 0,
    foreign key(user_id) references user(user_id) on update cascade on delete set null,
    foreign key(question_id) references question(question_id) on delete cascade on update cascade,
    foreign key(llm_id) references llm(llm_id) on update cascade on delete set null
);


create table if not exists user_question_upvote(
    upvote_id int AUTO_INCREMENT primary key,
    question_id int not null,
    user_id int not null,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade, 
    foreign key(question_id) references question(question_id) on delete cascade on update cascade
);

create table if not exists user_question_downvote(
    downvote_id int AUTO_INCREMENT primary key,
    question_id int not null,
    user_id int not null,
    foreign key(user_id) references user(user_id) on delete cascade on update cascade, 
    foreign key(question_id) references question(question_id) on delete cascade on update cascade
);

create table if not exists user_ranked_question(
    user_id int not null,
    question_id int not null,
    primary key(user_id, question_id),
    foreign key(user_id) references user(user_id) on delete cascade on update cascade, 
    foreign key(question_id) references question(question_id) on delete cascade on update cascade
)
