-- public.guilds definition

-- Drop table

-- DROP TABLE guilds;

CREATE TABLE guilds (
	id int8 NOT NULL,
	CONSTRAINT guilds_pkey PRIMARY KEY (id)
);


-- public.event_boosts definition

-- Drop table

-- DROP TABLE event_boosts;

CREATE TABLE event_boosts (
	id int8 NOT NULL,
	guild_id int8 NOT NULL,
	"text" text NOT NULL DEFAULT ''::text,
	CONSTRAINT byes_pkey_1 PRIMARY KEY (id),
	CONSTRAINT event_boosts_fk FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);


-- public.event_byes definition

-- Drop table

-- DROP TABLE event_byes;

CREATE TABLE event_byes (
	id int8 NOT NULL,
	guild_id int8 NOT NULL,
	"text" text NOT NULL DEFAULT ''::text,
	CONSTRAINT byes_pkey PRIMARY KEY (id),
	CONSTRAINT "FK_byes_guilds" FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);


-- public.event_welcomes definition

-- Drop table

-- DROP TABLE event_welcomes;

CREATE TABLE event_welcomes (
	id int8 NOT NULL,
	guild_id int8 NOT NULL,
	"text" text NOT NULL DEFAULT ''::text,
	CONSTRAINT welcomes_pkey PRIMARY KEY (id),
	CONSTRAINT "FK_welcomes_guilds" FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);


-- public."groups" definition

-- Drop table

-- DROP TABLE "groups";

CREATE TABLE "groups" (
	id serial NOT NULL,
	guild_id int8 NOT NULL,
	"name" text NOT NULL,
	description text NOT NULL,
	last_called timestamp NULL,
	CONSTRAINT groups_pkey PRIMARY KEY (id),
	CONSTRAINT "FK_groups_guilds" FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);


-- public.guild_members definition

-- Drop table

-- DROP TABLE guild_members;

CREATE TABLE guild_members (
	guild_id int8 NOT NULL,
	id int8 NOT NULL,
	CONSTRAINT guild_members_pkey PRIMARY KEY (guild_id, id),
	CONSTRAINT "FK_guild_members_guilds" FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX guild_members_guild_id_id_key ON public.guild_members USING btree (guild_id, id);


-- public.guild_settings definition

-- Drop table

-- DROP TABLE guild_settings;

CREATE TABLE guild_settings (
	guild_id int8 NOT NULL,
	"key" text NOT NULL DEFAULT ''::text,
	value text NOT NULL DEFAULT ''::text,
	CONSTRAINT guild_settings_guild_id_key_key UNIQUE (guild_id, key),
	CONSTRAINT "FK_guild_settings_guilds" FOREIGN KEY (guild_id) REFERENCES guilds(id) ON UPDATE RESTRICT ON DELETE CASCADE
);


-- public.roles_reaction definition

-- Drop table

-- DROP TABLE roles_reaction;

CREATE TABLE roles_reaction (
	guild_id int8 NOT NULL,
	message_id int8 NOT NULL,
	role_id int8 NOT NULL,
	reaction text NOT NULL,
	channel_id int8 NOT NULL,
	CONSTRAINT roles_reaction_un UNIQUE (guild_id, message_id, role_id, reaction, channel_id),
	CONSTRAINT roles_reaction_un2 UNIQUE (guild_id, message_id, role_id, channel_id),
	CONSTRAINT roles_reaction_fk FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);


-- public.birthdays definition

-- Drop table

-- DROP TABLE birthdays;

CREATE TABLE birthdays (
	guild_id int8 NOT NULL,
	member_id int8 NOT NULL,
	birthday date NOT NULL,
	timezone text NOT NULL DEFAULT 'CEST'::text,
	triggered bool NOT NULL DEFAULT false,
	given_role text NOT NULL DEFAULT ''::text,
	CONSTRAINT "FK_birthdays_guild_members" FOREIGN KEY (guild_id, member_id) REFERENCES guild_members(guild_id, id) ON DELETE CASCADE,
	CONSTRAINT "FK_birthdays_guilds" FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX birthdays_guild_id_member_id_key ON public.birthdays USING btree (guild_id, member_id);


-- public.group_members definition

-- Drop table

-- DROP TABLE group_members;

CREATE TABLE group_members (
	group_id int4 NOT NULL DEFAULT 0,
	member_id int8 NOT NULL,
	CONSTRAINT group_members_group_id_member_id_key UNIQUE (group_id, member_id),
	CONSTRAINT "FK_group_members_groups" FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);