drop database culturaLLM;
create database if not exists culturaLLM;
use culturaLLM;

create table if not exists user(
    user_id int AUTO_INCREMENT primary key,
    username varchar(255) unique not null,
    name varchar(255) not null,
    surname varchar(255) not null,
    bio text,
    --image_url text,
    password text not null,
    user_points int default 0,
    created_at timestamp default CURRENT_TIMESTAMP
    --last_login_at timestamp
);

create table if not exists question(
    question_id int AUTO_INCREMENT primary key,
    question_text text not null unique,
    created_by_user_id int,
    created_at timestamp CURRENT_TIMESTAMP,
    --answers_number int default 0,
    status ENUM('open','close') default 'open',
    foreign key(created_by_user_id) references user(user_id) on update cascade on delete set null
    --difficulty ENUM('hard','medium','easy'),
    --target_culture varchar(50) default 'italiana'
);

create table if not exists answer(
    answer_id int AUTO_INCREMENT primary key,
    answer_text text not null unique,
    answer_type ENUM('LLM','user'),
    created_at timestamp CURRENT_TIMESTAMP
    --is_culturally_specific_response boolean
)

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

create if not exists question_answer(
    question_id int not null,
    answer_id int not null,
    points int default 0,
    primary key(question_id,answer_id),
    foreign key(question_id) references question(question_id) on delete cascade on update cascade,
    foreign key(answer_id) references answer(answer_id) on delete cascade on update cascade
);

create if not exists user_answer_question(
    user_id int not null,
    answer_id int not null,
    question_id int not null,
    primary key(user_id,answer_id,question_id),
    foreign key(question_id) references question_answer(question_id) on delete cascade on update cascade,
    foreign key(answer_id) references question_answer(answer_id) on delete cascade on update cascade
    foreign key(user_id) references user(user_id) on delete cascade on update cascade
);