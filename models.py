from dataclasses import dataclass

@dataclass
class ParserParameters:
    parse_rate: int
    do_parse_frames: bool
    do_parse_kill_frames: bool
    trade_time: int
    round_buy_style: str
    are_damages_rolled_up: bool

@dataclass
class ServerVars:
    cash_bomb_defused: int
    cash_bomb_planted: int
    cash_team_t_win_bomb: int
    cash_win_defuse: int
    cash_win_time_run_out: int
    cash_win_elimination: int
    cash_player_killed_default: int
    cash_team_loser_bonus: int
    cash_team_loser_bonus_consecutive: int
    round_time: int
    round_time_defuse: int
    round_restart_delay: int
    freeze_time: int
    buy_time: int
    bomb_timer: int
    max_rounds: int
    timeouts_allowed: int
    coaching_allowed: int

@dataclass
class MatchPhases:
    announcement_last_round_half: list[int]
    announcement_final_round: list[int]
    announcement_match_started: list[int]
    round_started: list[int]
    round_ended: list[int]
    round_freeze_time_ended: list[int]
    round_ended_official: list[int]
    game_half_ended: list[int]
    match_start: list[int]
    match_started_changed: list[int]
    warmup_changed: list[int]
    team_switch: list[int]

@dataclass
class PlayerConnection:
    tick: int
    action: str # From what I can tell options are "connect" and "disconnect"
    steam_id: int

@dataclass
class Player:
    player_name: str
    steam_id: int

@dataclass
class Team:
    team_name: str
    players: list[Player]

@dataclass
class Kill:
    tick: int
    seconds: float
    clock_time: str
    attacker_steam_id: int
    attacker_name: str
    attacker_team: str
    attacker_side: str
    attacker_x: float
    attacker_y: float
    attacker_z: float
    attacker_view_x: float
    attacker_view_y: float
    victim_steam_id: int
    victim_name: str
    victim_team: str
    victim_side: str
    victim_x: float
    victim_y: float
    victim_z: float
    victim_view_x: float
    victim_view_y: float
    assister_steam_id: int | None
    assister_name: str | None
    assister_team: str | None
    assister_side: str | None
    is_suicide: bool
    is_teamkill: bool
    is_wallbang: bool
    penetrated_objects: int
    is_first_kill: bool
    is_headshot: bool
    is_victim_blinded: bool
    is_attacker_blinded: bool
    flash_thrower_steam_id: int | None
    flash_thrower_name: str | None
    flash_thrower_team: str | None
    flash_thrower_side: str | None
    is_no_scope: bool
    is_through_smoke: bool
    distance: float
    is_trade: bool
    player_traded_name: str | None
    player_traded_team: str | None
    player_traded_steam_id: int | None
    weapon: str
    weapon_class: str

@dataclass
class Damage:
    tick: int
    seconds: float
    clock_time: str
    attacker_steam_id: int
    attacker_name: str
    attacker_team: str
    attacker_side: str
    attacker_x: float
    attacker_y: float
    attacker_z: float
    attacker_view_x: float
    attacker_view_y: float
    is_attacker_strafe: bool # I don't entirely know what this refers to so maybe it should be did_attacker_strafe ?
    victim_steam_id: int
    victim_name: str
    victim_team: str
    victim_side: str
    victim_x: float
    victim_y: float
    victim_z: float
    victim_view_x: float
    victim_view_y: float
    weapon: str
    weapon_class: str
    hp_damage: int
    hp_damage_taken: int
    armor_damage: int
    armor_damage_taken: int
    hit_group: str
    is_friendly_fire: bool
    distance: float
    zoom_level: int

@dataclass
class Grenade:
    throw_tick: int
    destroy_tick: int
    throw_seconds: float
    throw_clock_time: str
    destroy_seconds: float
    destroy_clock_time: str
    thrower_steam_id: int
    thrower_name: str
    thrower_team: str
    thrower_side: str
    thrower_x: float
    thrower_y: float
    thrower_z: float
    grenade_type: str # i.e. "Flashbang", "Molotov", "HE Grenade", "Decoy Grenade", "Incendiary Grenade", etc.
    grenade_x: float
    grenade_y: float
    grenade_z: float
    entity_id: int

@dataclass
class BombEvent:
    tick: int
    seconds: float
    clock_time: str
    player_steam_id: int
    player_name: str
    player_team: str
    player_x: float
    player_y: float
    player_z: float
    bomb_action: str # i.e. "plant_begin", "plant_abort", TODO ADD MORE EXAMPLES?
    bomb_site: str # i.e. "A"

@dataclass
class WeaponFire:
    tick: int
    seconds: float
    clock_time: str
    player_steam_id: int
    player_name: str
    player_team: str
    player_side: str
    player_x: float
    player_y: float
    player_z: float
    player_view_x: float
    player_view_y: float
    is_player_strafe: bool
    weapon: str
    weapon_class: str
    ammo_in_magazine: int
    ammo_in_reserve: int
    zoom_level: int

@dataclass
class Flash:
    tick: int
    seconds: float
    clock_time: str
    attacker_steam_id: int
    attacker_name: str
    attacker_team: str
    attacker_side: str
    attacker_x: float
    attacker_y: float
    attacker_z: float
    attacker_view_x: float
    attacker_view_y: float
    player_steam_id: int
    player_name: str
    player_team: str
    player_side: str
    player_x: float
    player_y: float
    player_z: float
    player_view_x: float
    player_view_y: float
    flash_duration: float

@dataclass
class Weapon:
    weapon_name: str
    weapon_class: str
    ammo_in_magazine: int
    ammo_in_reserve: int

@dataclass
class PlayerFrameState:
    """
    Data about a player, a snapshot of their metrics during one frame.
    """
    steam_id: int
    name: str
    team: str
    side: str
    x: float
    y: float
    z: float
    velocity_x: float
    velocity_y: float
    velocity_z: float
    view_x: float
    view_y: float
    hp: int
    armor: int
    active_weapon: str
    total_utility: int
    is_alive: bool
    is_blinded: bool
    is_airborne: bool
    is_ducking: bool
    is_ducking_in_progress: bool
    is_unducking_in_progress: bool
    is_defusing: bool
    is_planting: bool
    is_reloading: bool
    is_in_bomb_zone: bool
    is_in_buy_zone: bool
    is_standing: bool
    is_scoped: bool
    is_walking: bool
    is_unknown: bool # What is this? LOL
    inventory: list[Weapon] | None
    spotters: list # I don't know what this is a list of yet TODO
    equipment_value: int
    equipment_value_freeze_time_end: int
    equipment_value_round_start: int
    cash: int
    cash_spend_this_round: int
    cash_spend_total: int
    has_helmet: bool
    has_defuse_kit: bool
    has_bomb: bool
    ping: int
    zoom_level: int

@dataclass
class TeamFrameState:
    """
    Data about a team, a snapshot of their metrics during one frame.
    """
    side: str
    team_name: str
    team_eq_val: int # The value of the team's equipment
    alive_players: int
    total_utility: int # The amount of utility items the team owns
    players: list[PlayerFrameState]

@dataclass
class Bomb:
    x: float
    y: float
    z: float

@dataclass
class Projectile:
    projectile_type: str # i.e. "Smoke Grenade"
    x: float
    y: float
    z: float

@dataclass
class Smoke:
    grenade_entity_id: int
    start_tick: int
    x: float
    y: float
    z: float

@dataclass
class Fire:
    unique_id: int
    x: float
    y: float
    z: float

@dataclass
class Frame:
    is_kill_frame: bool
    tick: int
    seconds: float
    clock_time: str
    t: TeamFrameState
    ct: TeamFrameState
    bomb_planted: bool
    bomb_site: str
    bomb: Bomb
    projectiles: list[Projectile]
    smokes: list[Smoke]
    fires: list[Fire]

@dataclass
class Round:
    round_number: int
    is_warmup: bool
    start_tick: int
    freeze_time_end_tick: int
    end_tick: int
    end_official_tick: int
    bomb_plant_tick: int | None
    t_score: int
    ct_score: int
    end_t_score: int
    end_ct_score: int
    ct_team: str # Team name (i.e. 'Cloud9')
    t_team: str # Team name (i.e. 'Outsiders')
    winning_side: str # "CT" or "T"
    winning_team: str # Team name (i.e. 'Cloud9')
    losing_team: str # Team name (i.e. 'Outsiders')
    round_end_reason: str
    ct_freeze_time_end_eq_val: int # The value of the CT team's inventory at the end of freeze time
    ct_round_start_eq_val: int # The value of the CT team's inventory at the start of the round
    ct_round_spend_money: int # The amount of money spent by the CT team in the round
    ct_buy_type: str # A description of the CT team's buy type (i.e. "Full Eco")
    t_freeze_time_end_eq_val: int # The value of the T team's inventory at the end of freeze time
    t_round_start_eq_val: int # The value of the T team's inventory at the start of the round
    t_round_spend_money: int # The amount of money spent by the T team in the round
    t_buy_type: str # A description of the T team's buy type (i.e. "Full Eco")
    ct_side: Team
    t_side: Team
    kills: list[Kill]
    damages: list[Damage]
    grenades: list[Grenade]
    bomb_events: list[BombEvent]
    weapon_fires: list[WeaponFire]
    flashes: list[Flash]
    frames: list[Frame]

@dataclass
class Demo:
    match_id: str
    client_name: str
    map_name: str
    tick_rate: int
    playback_ticks: int
    playback_frames_count: int
    parsed_to_frame_index: int
    parser_parameters: ParserParameters
    server_vars: ServerVars
    match_phases: MatchPhases
    matchmaking_ranks: list # Not sure what the type of is so not specifying
    player_connections: list[PlayerConnection]
    game_rounds: list[Round]
