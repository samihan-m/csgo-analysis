from awpy.parser import DemoParser
from dataclasses import fields
import csv
import logging
import plotting
import mathing
import models
from mathing import PlayerState, TeamArea


def parse_demo_file(demo_file_name: str) -> dict:
    """
    Given a demo file name, parse it and return the data
    """
    logging.debug("Reached inside of  parse_demo_file")
    # 128 parse_rate ideally matches with the 128 ticks per second of the demo file to mean player position is polled every second
    p = DemoParser(demofile=demo_file_name, parse_rate=128, parse_frames=True)
    logging.debug("Constructed DemoParser")
    data = p.parse()
    logging.debug("Parsed demo file")
    return data

def extract_player_information(demo_file_data) -> list:
    """
    Given a parsed demo file, extract player states from it and return a list of PlayerState information
    """

    player_information: list[PlayerState] = []

    data = demo_file_data

    for game_round_index in range(0, len(data["gameRounds"])):
        frames = data["gameRounds"][game_round_index]["frames"]
        for frame in frames:
            for team in ["ct", "t"]:
                for player in frame[team]["players"]:
                    player_information.append(PlayerState(game_round_index, player["name"], team, player["x"], player["y"], player["z"]))

    return player_information

def write_player_information_to_csv(player_information: list[PlayerState], csv_file_name: str) -> None:
    """
    Provided a list of player information, write it to a csv file
    """
    with open(csv_file_name, "w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow([class_field.name for class_field in fields(PlayerState)])
        for state_entry in player_information:
            writer.writerow([getattr(state_entry, field_name) for field_name in [class_field.name for class_field in fields(PlayerState)]])

def write_area_controlled_information_to_csv(controlled_area_information: dict, csv_file_name: str) -> None:
    with open(csv_file_name, "w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow([class_field.name for class_field in fields(TeamArea)])
        for area_entry in controlled_area_information:
            writer.writerow([getattr(area_entry, field_name) for field_name in [class_field.name for class_field in fields(TeamArea)]])

def deserialize_demo_data(demo_file_data: dict) -> models.Demo:
    player_connections: list[models.PlayerConnection] = []
    for connection in demo_file_data["playerConnections"]:
        player_connections.append(
            models.PlayerConnection(
                tick=connection["tick"],
                action=connection["action"],
                steam_id=connection["steamID"],
            )
        )

    game_rounds: list[models.Round] = []
    for round in demo_file_data["gameRounds"]:
        ct_side: models.Team
        t_side: models.Team

        ct_players: list[models.Player] = []
        for player in round["ctSide"]["players"]:
            ct_players.append(models.Player(
                player_name=player["playerName"],
                steam_id=player["steamID"],
            ))
        ct_side = models.Team(
            team_name=round["ctSide"]["teamName"],
            players=ct_players,
        )

        t_players: list[models.Player] = []
        for player in round["tSide"]["players"]:
            t_players.append(models.Player(
                player_name=player["playerName"],
                steam_id=player["steamID"],
            ))
        t_side = models.Team(
            team_name=round["tSide"]["teamName"],
            players=t_players,
        )

        kills: list[models.Kill] = []
        for kill in round["kills"]:
            kills.append(models.Kill(
                tick=kill["tick"],
                seconds=kill["seconds"],
                clock_time=kill["clockTime"],
                attacker_steam_id=kill["attackerSteamID"],
                attacker_name=kill["attackerName"],
                attacker_team=kill["attackerTeam"],
                attacker_side=kill["attackerSide"],
                attacker_x=kill["attackerX"],
                attacker_y=kill["attackerY"],
                attacker_z=kill["attackerZ"],
                attacker_view_x=kill["attackerViewX"],
                attacker_view_y=kill["attackerViewY"],
                victim_steam_id=kill["victimSteamID"],
                victim_name=kill["victimName"],
                victim_team=kill["victimTeam"],
                victim_side=kill["victimSide"],
                victim_x=kill["victimX"],
                victim_y=kill["victimY"],
                victim_z=kill["victimZ"],
                victim_view_x=kill["victimViewX"],
                victim_view_y=kill["victimViewY"],
                assister_steam_id=kill["assisterSteamID"],
                assister_name=kill["assisterName"],
                assister_team=kill["assisterTeam"],
                assister_side=kill["assisterSide"],
                is_suicide=kill["isSuicide"],
                is_teamkill=kill["isTeamkill"],
                is_wallbang=kill["isWallbang"],
                penetrated_objects=kill["penetratedObjects"],
                is_first_kill=kill["isFirstKill"],
                is_headshot=kill["isHeadshot"],
                is_victim_blinded=kill["victimBlinded"],
                is_attacker_blinded=kill["attackerBlinded"],
                flash_thrower_steam_id=kill["flashThrowerSteamID"],
                flash_thrower_name=kill["flashThrowerName"],
                flash_thrower_team=kill["flashThrowerTeam"],
                flash_thrower_side=kill["flashThrowerSide"],
                is_no_scope=kill["noScope"],
                is_through_smoke=kill["thruSmoke"],
                distance=kill["distance"],
                is_trade=kill["isTrade"],
                player_traded_name=kill["playerTradedName"],
                player_traded_team=kill["playerTradedTeam"],
                player_traded_steam_id=kill["playerTradedSteamID"],
                weapon=kill["weapon"],
                weapon_class=kill["weaponClass"],
            ))

        damages: list[models.Damage] = []
        for damage in round["damages"]:
            damages.append(models.Damage(
                tick=damage["tick"],
                seconds=damage["seconds"],
                clock_time=damage["clockTime"],
                attacker_steam_id=damage["attackerSteamID"],
                attacker_name=damage["attackerName"],
                attacker_team=damage["attackerTeam"],
                attacker_side=damage["attackerSide"],
                attacker_x=damage["attackerX"],
                attacker_y=damage["attackerY"],
                attacker_z=damage["attackerZ"],
                attacker_view_x=damage["attackerViewX"],
                attacker_view_y=damage["attackerViewY"],
                is_attacker_strafe=damage["attackerStrafe"],
                victim_steam_id=damage["victimSteamID"],
                victim_name=damage["victimName"],
                victim_team=damage["victimTeam"],
                victim_side=damage["victimSide"],
                victim_x=damage["victimX"],
                victim_y=damage["victimY"],
                victim_z=damage["victimZ"],
                victim_view_x=damage["victimViewX"],
                victim_view_y=damage["victimViewY"],
                weapon=damage["weapon"],
                weapon_class=damage["weaponClass"],
                hp_damage=damage["hpDamage"],
                hp_damage_taken=damage["hpDamageTaken"],
                armor_damage=damage["armorDamage"],
                armor_damage_taken=damage["armorDamageTaken"],
                hit_group=damage["hitGroup"],
                is_friendly_fire=damage["isFriendlyFire"],
                distance=damage["distance"],
                zoom_level=damage["zoomLevel"],
            ))

        grenades: list[models.Grenade] = []
        for grenade in round["grenades"]:
            grenades.append(models.Grenade(
                throw_tick=grenade["throwTick"],
                destroy_tick=grenade["destroyTick"],
                throw_seconds=grenade["throwSeconds"],
                throw_clock_time=grenade["throwClockTime"],
                destroy_seconds=grenade["destroySeconds"],
                destroy_clock_time=grenade["destroyClockTime"],
                thrower_steam_id=grenade["throwerSteamID"],
                thrower_name=grenade["throwerName"],
                thrower_team=grenade["throwerTeam"],
                thrower_side=grenade["throwerSide"],
                thrower_x=grenade["throwerX"],
                thrower_y=grenade["throwerY"],
                thrower_z=grenade["throwerZ"],
                grenade_type=grenade["grenadeType"],
                grenade_x=grenade["grenadeX"],
                grenade_y=grenade["grenadeY"],
                grenade_z=grenade["grenadeZ"],
                entity_id=grenade["entityId"],
            ))

        bomb_events: list[models.BombEvent] = []
        for bomb_event in round["bombEvents"]:
            bomb_events.append(models.BombEvent(
                tick=bomb_event["tick"],
                seconds=bomb_event["seconds"],
                clock_time=bomb_event["clockTime"],
                player_steam_id=bomb_event["playerSteamID"],
                player_name=bomb_event["playerName"],
                player_team=bomb_event["playerTeam"],
                player_x=bomb_event["playerX"],
                player_y=bomb_event["playerY"],
                player_z=bomb_event["playerZ"],
                bomb_action=bomb_event["bombAction"],
                bomb_site=bomb_event["bombSite"],
            ))

        weapon_fires: list[models.WeaponFire] = []
        for weapon_fire in round["weaponFires"]:
            weapon_fires.append(models.WeaponFire(
                tick=weapon_fire["tick"],
                seconds=weapon_fire["seconds"],
                clock_time=weapon_fire["clockTime"],
                player_steam_id=weapon_fire["playerSteamID"],
                player_name=weapon_fire["playerName"],
                player_team=weapon_fire["playerTeam"],
                player_side=weapon_fire["playerSide"],
                player_x=weapon_fire["playerX"],
                player_y=weapon_fire["playerY"],
                player_z=weapon_fire["playerZ"],
                player_view_x=weapon_fire["playerViewX"],
                player_view_y=weapon_fire["playerViewY"],
                is_player_strafe=weapon_fire["playerStrafe"],
                weapon=weapon_fire["weapon"],
                weapon_class=weapon_fire["weaponClass"],
                ammo_in_magazine=weapon_fire["ammoInMagazine"],
                ammo_in_reserve=weapon_fire["ammoInReserve"],
                zoom_level=weapon_fire["zoomLevel"],
            ))

        flashes: list[models.Flash] = []
        for flash in round["flashes"]:
            flashes.append(models.Flash(
                tick=flash["tick"],
                seconds=flash["seconds"],
                clock_time=flash["clockTime"],
                attacker_steam_id=flash["attackerSteamID"],
                attacker_name=flash["attackerName"],
                attacker_team=flash["attackerTeam"],
                attacker_side=flash["attackerSide"],
                attacker_x=flash["attackerX"],
                attacker_y=flash["attackerY"],
                attacker_z=flash["attackerZ"],
                attacker_view_x=flash["attackerViewX"],
                attacker_view_y=flash["attackerViewY"],
                player_steam_id=flash["playerSteamID"],
                player_name=flash["playerName"],
                player_team=flash["playerTeam"],
                player_side=flash["playerSide"],
                player_x=flash["playerX"],
                player_y=flash["playerY"],
                player_z=flash["playerZ"],
                player_view_x=flash["playerViewX"],
                player_view_y=flash["playerViewY"],
                flash_duration=flash["flashDuration"],
            ))

        frames: list[models.Frame] = []
        for frame in round["frames"]:
            t: models.TeamFrameState
            
            t_players: list[models.PlayerFrameState] = []
            for player in frame["t"]["players"]:
                inventory: list[models.Weapon] = []
                for weapon in player["inventory"] or []:
                    inventory.append(models.Weapon(
                        weapon_name=weapon["weaponName"],
                        weapon_class=weapon["weaponClass"],
                        ammo_in_magazine=weapon["ammoInMagazine"],
                        ammo_in_reserve=weapon["ammoInReserve"],
                    ))

                t_players.append(models.PlayerFrameState(
                    steam_id=player["steamID"],
                    name=player["name"],
                    team=player["team"],
                    side=player["side"],
                    x=player["x"],
                    y=player["y"],
                    z=player["z"],
                    velocity_x=player["velocityX"],
                    velocity_y=player["velocityY"],
                    velocity_z=player["velocityZ"],
                    view_x=player["viewX"],
                    view_y=player["viewY"],
                    hp=player["hp"],
                    armor=player["armor"],
                    active_weapon=player["activeWeapon"],
                    total_utility=player["totalUtility"],
                    is_alive=player["isAlive"],
                    is_blinded=player["isBlinded"],
                    is_airborne=player["isAirborne"],
                    is_ducking=player["isDucking"],
                    is_ducking_in_progress=player["isDuckingInProgress"],
                    is_unducking_in_progress=player["isUnDuckingInProgress"],
                    is_defusing=player["isDefusing"],
                    is_planting=player["isPlanting"],
                    is_reloading=player["isReloading"],
                    is_in_bomb_zone=player["isInBombZone"],
                    is_in_buy_zone=player["isInBuyZone"],
                    is_standing=player["isStanding"],
                    is_scoped=player["isScoped"],
                    is_walking=player["isWalking"],
                    is_unknown=player["isUnknown"],
                    inventory=inventory,
                    spotters=player["spotters"],
                    equipment_value=player["equipmentValue"],
                    equipment_value_freeze_time_end=player["equipmentValueFreezetimeEnd"],
                    equipment_value_round_start=player["equipmentValueRoundStart"],
                    cash=player["cash"],
                    cash_spend_this_round=player["cashSpendThisRound"],
                    cash_spend_total=player["cashSpendTotal"],
                    has_helmet=player["hasHelmet"],
                    has_defuse_kit=player["hasDefuse"],
                    has_bomb=player["hasBomb"],
                    ping=player["ping"],
                    zoom_level=player["zoomLevel"],
                ))

            t = models.TeamFrameState(
                side=frame["t"]["side"],
                team_name=frame["t"]["teamName"],
                team_eq_val=frame["t"]["teamEqVal"],
                alive_players=frame["t"]["alivePlayers"],
                total_utility=frame["t"]["totalUtility"],
                players=t_players,
            )

            ct: models.TeamFrameState
            
            ct_players: list[models.PlayerFrameState] = []
            for player in frame["ct"]["players"]:
                inventory: list[models.Weapon] = []
                for weapon in player["inventory"] or []:
                    inventory.append(models.Weapon(
                        weapon_name=weapon["weaponName"],
                        weapon_class=weapon["weaponClass"],
                        ammo_in_magazine=weapon["ammoInMagazine"],
                        ammo_in_reserve=weapon["ammoInReserve"],
                    ))

                ct_players.append(models.PlayerFrameState(
                    steam_id=player["steamID"],
                    name=player["name"],
                    team=player["team"],
                    side=player["side"],
                    x=player["x"],
                    y=player["y"],
                    z=player["z"],
                    velocity_x=player["velocityX"],
                    velocity_y=player["velocityY"],
                    velocity_z=player["velocityZ"],
                    view_x=player["viewX"],
                    view_y=player["viewY"],
                    hp=player["hp"],
                    armor=player["armor"],
                    active_weapon=player["activeWeapon"],
                    total_utility=player["totalUtility"],
                    is_alive=player["isAlive"],
                    is_blinded=player["isBlinded"],
                    is_airborne=player["isAirborne"],
                    is_ducking=player["isDucking"],
                    is_ducking_in_progress=player["isDuckingInProgress"],
                    is_unducking_in_progress=player["isUnDuckingInProgress"],
                    is_defusing=player["isDefusing"],
                    is_planting=player["isPlanting"],
                    is_reloading=player["isReloading"],
                    is_in_bomb_zone=player["isInBombZone"],
                    is_in_buy_zone=player["isInBuyZone"],
                    is_standing=player["isStanding"],
                    is_scoped=player["isScoped"],
                    is_walking=player["isWalking"],
                    is_unknown=player["isUnknown"],
                    inventory=inventory,
                    spotters=player["spotters"],
                    equipment_value=player["equipmentValue"],
                    equipment_value_freeze_time_end=player["equipmentValueFreezetimeEnd"],
                    equipment_value_round_start=player["equipmentValueRoundStart"],
                    cash=player["cash"],
                    cash_spend_this_round=player["cashSpendThisRound"],
                    cash_spend_total=player["cashSpendTotal"],
                    has_helmet=player["hasHelmet"],
                    has_defuse_kit=player["hasDefuse"],
                    has_bomb=player["hasBomb"],
                    ping=player["ping"],
                    zoom_level=player["zoomLevel"],
                ))

            ct = models.TeamFrameState(
                side=frame["ct"]["side"],
                team_name=frame["ct"]["teamName"],
                team_eq_val=frame["ct"]["teamEqVal"],
                alive_players=frame["ct"]["alivePlayers"],
                total_utility=frame["ct"]["totalUtility"],
                players=t_players,
            )

            projectiles: list[models.Projectile] = []
            for projectile in frame["projectiles"]:
                projectiles.append(models.Projectile(
                    projectile_type=projectile["projectileType"],
                    x=projectile["x"],
                    y=projectile["y"],
                    z=projectile["z"],
                ))

            smokes: list[models.Smoke] = []
            for smoke in frame["smokes"]:
                smokes.append(models.Smoke(
                    grenade_entity_id=smoke["grenadeEntityID"],
                    start_tick=smoke["startTick"],
                    x=smoke["x"],
                    y=smoke["y"],
                    z=smoke["z"],
                ))

            fires: list[models.Fire] = []
            for fire in frame["fires"]:
                fires.append(models.Fire(
                    unique_id=fire["uniqueID"],
                    x=fire["x"],
                    y=fire["y"],
                    z=fire["z"],
                ))

            frames.append(models.Frame(
                is_kill_frame = frame["isKillFrame"],
                tick=frame["tick"],
                seconds=frame["seconds"],
                clock_time=frame["clockTime"],
                t=t,
                ct=ct,
                bomb_planted=frame["bombPlanted"],
                bomb_site=frame["bombsite"],
                bomb=models.Bomb(
                    x=frame["bomb"]["x"],
                    y=frame["bomb"]["y"],
                    z=frame["bomb"]["z"],
                ),
                projectiles=projectiles,
                smokes=smokes,
                fires=fires
            ))

        game_rounds.append(models.Round(
            round_number=round["roundNum"],
            is_warmup=round["isWarmup"],
            start_tick=round["startTick"],
            freeze_time_end_tick=round["freezeTimeEndTick"],
            end_tick=round["endTick"],
            end_official_tick=round["endOfficialTick"],
            bomb_plant_tick=round["bombPlantTick"],
            t_score=round["tScore"],
            ct_score=round["ctScore"],
            end_t_score=round["endTScore"],
            end_ct_score=round["endCTScore"],
            ct_team=round["ctTeam"],
            t_team=round["tTeam"],
            winning_side=round["winningSide"],
            winning_team=round["winningTeam"],
            losing_team=round["losingTeam"],
            round_end_reason=round["roundEndReason"],
            ct_freeze_time_end_eq_val=round["ctFreezeTimeEndEqVal"],
            ct_round_start_eq_val=round["ctRoundStartEqVal"],
            ct_round_spend_money=round["ctRoundSpendMoney"],
            ct_buy_type=round["ctBuyType"],
            t_freeze_time_end_eq_val=round["tFreezeTimeEndEqVal"],
            t_round_start_eq_val=round["tRoundStartEqVal"],
            t_round_spend_money=round["tRoundSpendMoney"],
            t_buy_type=round["tBuyType"],
            ct_side=ct_side,
            t_side=t_side,
            kills=kills,
            damages=damages,
            grenades=grenades,
            bomb_events=bomb_events,
            weapon_fires=weapon_fires,
            flashes=flashes,
            frames=frames,
        ))

    structured_demo = models.Demo(
        match_id=demo_file_data["matchID"],
        client_name=demo_file_data["clientName"],
        map_name=demo_file_data["mapName"],
        tick_rate=demo_file_data["tickRate"],
        playback_ticks=demo_file_data["playbackTicks"],
        playback_frames_count=demo_file_data["playbackFramesCount"],
        parsed_to_frame_index=demo_file_data["parsedToFrameIdx"],
        parser_parameters=models.ParserParameters(
            parse_rate=demo_file_data["parserParameters"]["parseRate"],
            do_parse_frames=demo_file_data["parserParameters"]["parseFrames"],
            do_parse_kill_frames=demo_file_data["parserParameters"]["parseKillFrames"],
            trade_time=demo_file_data["parserParameters"]["tradeTime"],
            round_buy_style=demo_file_data["parserParameters"]["roundBuyStyle"],
            are_damages_rolled_up=demo_file_data["parserParameters"]["damagesRolledUp"],
        ),
        server_vars=models.ServerVars(
            cash_bomb_defused=demo_file_data["serverVars"]["cashBombDefused"],
            cash_bomb_planted=demo_file_data["serverVars"]["cashBombPlanted"],
            cash_team_t_win_bomb=demo_file_data["serverVars"]["cashTeamTWinBomb"],
            cash_win_defuse=demo_file_data["serverVars"]["cashWinDefuse"],
            cash_win_time_run_out=demo_file_data["serverVars"]["cashWinTimeRunOut"],
            cash_win_elimination=demo_file_data["serverVars"]["cashWinElimination"],
            cash_player_killed_default=demo_file_data["serverVars"]["cashPlayerKilledDefault"],
            cash_team_loser_bonus=demo_file_data["serverVars"]["cashTeamLoserBonus"],
            cash_team_loser_bonus_consecutive=demo_file_data["serverVars"]["cashTeamLoserBonusConsecutive"],
            round_time=demo_file_data["serverVars"]["roundTime"],
            round_time_defuse=demo_file_data["serverVars"]["roundTimeDefuse"],
            round_restart_delay=demo_file_data["serverVars"]["roundRestartDelay"],
            freeze_time=demo_file_data["serverVars"]["freezeTime"],
            buy_time=demo_file_data["serverVars"]["buyTime"],
            bomb_timer=demo_file_data["serverVars"]["bombTimer"],
            max_rounds=demo_file_data["serverVars"]["maxRounds"],
            timeouts_allowed=demo_file_data["serverVars"]["timeoutsAllowed"],
            coaching_allowed=demo_file_data["serverVars"]["coachingAllowed"],
        ),
        match_phases=models.MatchPhases(
            announcement_last_round_half=demo_file_data["matchPhases"]["announcementLastRoundHalf"],
            announcement_final_round=demo_file_data["matchPhases"]["announcementFinalRound"],
            announcement_match_started=demo_file_data["matchPhases"]["announcementMatchStarted"],
            round_started=demo_file_data["matchPhases"]["roundStarted"],
            round_ended=demo_file_data["matchPhases"]["roundEnded"],
            round_freeze_time_ended=demo_file_data["matchPhases"]["roundFreezetimeEnded"],
            round_ended_official=demo_file_data["matchPhases"]["roundEndedOfficial"],
            game_half_ended=demo_file_data["matchPhases"]["gameHalfEnded"],
            match_start=demo_file_data["matchPhases"]["matchStart"],
            match_started_changed=demo_file_data["matchPhases"]["matchStartedChanged"],
            warmup_changed=demo_file_data["matchPhases"]["warmupChanged"],
            team_switch=demo_file_data["matchPhases"]["teamSwitch"],
        ),
        matchmaking_ranks=demo_file_data["matchmakingRanks"],
        player_connections=player_connections,
        game_rounds=game_rounds,
    )

    print(structured_demo)

def main():
    demo_file_name = r"D:/Samihan/Documents/Programming/Python Projects/CSGO Demo Parsing/demos/cloud9-vs-outsiders-m1-dust2.dem"
    print(f"Parsing {demo_file_name}")
    data = parse_demo_file(demo_file_name)
    print(data.keys())

    print(f"Plotting rounds for {demo_file_name}")

    # plotting.plot_rounds(data, "cloud9-vs-outsiders-m1-dust2")
    # plotting.plot_first_round(data, "testing-fill-2")

    first_frame = data["gameRounds"][0]["frames"][0]

    # print(first_frame)

    # outer_points = mathing.get_outer_team_points(first_frame)
    # print(mathing.get_covered_area_between_points(first_frame, data["mapName"]))

    # print("Processing full game now")
    # area_data = mathing.get_area_controlled_information_for_game(data)
    # write_area_controlled_information_to_csv(area_data, "cloud9-vs-outsiders-m1-dust2-controlled-area.csv")
    # print("Wrote data.")
    

if __name__ == "__main__":
    main()
