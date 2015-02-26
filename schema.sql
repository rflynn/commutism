
pragma page_size = 4096;

begin;

drop table if exists usertrack;
create table usertrack (
    id          integer primary key autoincrement,
    ts          integer not null,
    uid         bigint  not null,
    lat         float   not null,
    long_       float   not null,
    acc         integer not null
);

commit;

