delete from public."Descriptor" where opus_id in 
(select id from public."Opus" where ref like 'tstneuma%');

delete from public."Bookmark" where opus_id in 
(select id from public."Opus" where ref like 'tstneuma%');

delete from public."Opus" where ref like 'tstneuma%';  