"""Build ZIP Bomb assets from installed PDXRP definitions; run from the mod root."""
from pathlib import Path
import re
import shutil
from PIL import Image

MOD = Path(__file__).resolve().parents[1]
GAME = Path(r"C:\Steam\steamapps\common\Victoria 3\game")

def block(text, key):
    match = re.search(r"(?m)^" + re.escape(key) + r"\s*=\s*\{", text)
    if not match:
        raise ValueError(key)
    start = text.index("{", match.start())
    depth = 1
    end = start + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start + 1:end - 1]

def write(relative, text, localization=False):
    path = MOD / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8-sig")

write("common/country_definitions/pdxrp_zip_bomb.txt", """
ZIP = {
    color = { 0 0 0 }
    country_type = recognized
    tier = kingdom
    cultures = { baganda }
    religion = gnu_linux
    capital = STATE_UGANDA
}
""")

# Keep the culture key so existing pops, homelands and country references work.
culture = block((GAME / "common/cultures/00_cultures.txt").read_text(encoding="utf-8-sig"), "baganda")
culture = culture.replace("heritage_eastern_bantu", "heritage_virtual").replace("language_lacustrine_bantu", "language_assembly")
culture = culture.replace("1 = african", "1 = promethean_ethnicity").replace("graphics = african", "graphics = european")
culture = culture.replace("religion = animist", "religion = gnu_linux")
for name_list in ["male_common_first_names", "female_common_first_names"]:
    culture = re.sub(name_list + r"\s*=\s*\{[^}]*\}", name_list + " = { pdxrp_pop_character_name }", culture)
for name_list in ["noble_last_names", "common_last_names"]:
    culture = re.sub(name_list + r"\s*=\s*\{[^}]*\}", name_list + " = { pdxrp_pop_empty_surname }", culture)
write("common/cultures/pdxrp_zip_bomb.txt", "REPLACE:baganda = {" + culture + "}\n")
write("common/religions/pdxrp_zip_bomb.txt", """
gnu_linux = {
    icon = "gfx/interface/icons/religion_icons/atheist.dds"
    heritage = heritage_materialist
    color = { 0.1 0.1 0.1 }
}
""")
write("common/discrimination_trait_groups/pdxrp_zip_bomb.txt", """
heritage_group_virtual = { type = heritage }
language_group_assembly = { type = language }
""")
write("common/discrimination_traits/pdxrp_zip_bomb.txt", """
heritage_virtual = { type = heritage trait_group = heritage_group_virtual }
language_assembly = { type = language trait_group = language_group_assembly }
""")
write("common/static_modifiers/pdxrp_zip_bomb.txt", """
pdxrp_zip_bomb_collective = {
    state_food_security_add = 1.0
    state_working_adult_ratio_add = 0.50
    country_minting_add = 10000000
    country_construction_add = 2500
    country_max_weekly_construction_progress_add = 50
    country_bureaucracy_add = 10000
    country_weekly_innovation_add = 200
    state_lower_strata_expected_sol_add = -8
    building_training_rate_mult = 3.0
    state_education_access_add = 1.0
    state_literacy_growth_add = 0.10
    state_assimilation_mult = 3.0
    state_allow_assimilation_in_homeland_bool = yes
    character_command_limit_mult = 1.0
    # Mass conscription supplies the other 100 levels of the 1,000-level cap.
    state_building_barrack_max_level_add = 900
}
""")

# Script-only technology gates the unique units without changing other countries.
data_center_goods = [
    "wood", "hardwood", "fabric", "iron", "coal", "sulfur", "lead", "rubber", "oil",
    "steel", "glass", "tools", "paper", "fertilizer", "explosives", "engines",
    "automobiles", "electricity", "telephones", "radios", "groceries", "meat",
    "ammunition", "small_arms", "artillery", "tanks", "aeroplanes",
    "clippers", "steamers", "merchant_marine",
]
write("common/building_groups/pdxrp_zip_bomb.txt", """
bg_zip_data_centers = {
    parent_group = bg_manufacturing
    lens = heavy_industry
    urbanization = 20
    economy_of_scale = no
    infrastructure_usage_per_level = 1
}
""")
write("common/buildings/pdxrp_zip_bomb.txt", """
building_zip_data_center = {
    building_group = bg_zip_data_centers
    icon = "gfx/interface/icons/building_icons/electrics_industry.dds"
    city_type = city
    levels_per_mesh = 5
    required_construction = 500
    ownership_type = self
    production_method_groups = { pmg_zip_data_center }
    potential = { owner = { c:ZIP ?= THIS } }
    ai_value = 1000
    background = "gfx/interface/icons/building_icons/backgrounds/building_panel_bg_heavy_industry.dds"
}
""")
write("common/production_method_groups/pdxrp_zip_bomb.txt", """
pmg_zip_data_center = {
    texture = "gfx/interface/icons/generic_icons/mixed_icon_base.dds"
    production_methods = { pm_zip_data_center }
}
""")
write("common/production_methods/pdxrp_zip_bomb.txt", """
pm_zip_data_center = {
    texture = "gfx/interface/icons/building_icons/electrics_industry.dds"
    is_default = yes
    building_modifiers = {
        level_scaled = {
            building_employment_laborers_add = 80000
            building_employment_clerks_add = 15000
            building_employment_engineers_add = 5000
        }
        workforce_scaled = {
            goods_output_grain_add = 500
""" + "\n".join("            goods_output_" + good + "_add = 25" for good in data_center_goods) + """
        }
    }
}
""")

write("common/technology/technologies/pdxrp_zip_bomb.txt", """
pdxrp_zip_bomb_virtual_arsenal = {
    era = era_1
    category = military
    texture = "gfx/interface/icons/invention_icons/standing_army.dds"
    can_research = no
    ai_weight = { value = 0 }
}
""")
land = (MOD / "common/combat_unit_types/00_land_combat_unit_types.txt").read_text(encoding="utf-8-sig")
units = []
for source, target in [
    ("combat_unit_type_mechanized_infantry", "combat_unit_type_zip_binary_troopers"),
    ("combat_unit_type_heavy_tank", "combat_unit_type_zip_file_corruptors"),
    ("combat_unit_type_light_tanks", "combat_unit_type_zip_katla_cultist_magi"),
]:
    body = block(land, source)
    body = re.sub(r"unlocking_technologies\s*=\s*\{[^}]*\}", "unlocking_technologies = { pdxrp_zip_bomb_virtual_arsenal }", body)
    body = re.sub(r"upkeep_modifier\s*=\s*\{[^}]*\}", "upkeep_modifier = { goods_input_grain_add = 1 }", body)
    units.append(target + " = {" + body + "}")
write("common/combat_unit_types/zz_pdxrp_zip_bomb.txt", "\n\n".join(units))
ships = (MOD / "common/ship_types/00_ship_types.txt").read_text(encoding="utf-8-sig")
# Preserve ship modification stats, but strip their extra goods costs for ZIP.
modification_sources = {}
for directory in [GAME / "common/ship_modifications", MOD / "common/ship_modifications"]:
    for file in directory.glob("*.txt"):
        text = file.read_text(encoding="utf-8-sig")
        for match in re.finditer(r"(?m)^((?:(?:REPLACE|REPLACE_OR_CREATE):)?([A-Za-z0-9_]+))\s*=\s*\{", text):
            modification_sources[match[2]] = block(text, match[1])
zip_modifications = {}
navy = []
for source, target in [
    ("ship_type_super_dreadnought", "ship_type_zip_linux_ship"),
    ("ship_type_aircraft_carrier", "ship_type_zip_dragon_carrier"),
]:
    body = block(ships, source)
    body = re.sub(r"unlocking_technologies\s*=\s*\{[^}]*\}", "unlocking_technologies = { pdxrp_zip_bomb_virtual_arsenal }", body)
    body = re.sub(r"construction_goods\s*=\s*\{[^}]*\}", "construction_goods = { goods_input_meat_add = 1 }", body)
    body = re.sub(r"materiel_goods\s*=\s*\{[^}]*\}", "materiel_goods = { goods_input_grain_add = 1 }", body)
    for key in set(re.findall(r"\b[A-Za-z0-9_]+\b", body)) & modification_sources.keys():
        zip_key = "pdxrp_zip_" + key
        mod_body = modification_sources[key]
        mod_body = re.sub(r"(?:construction_goods|materiel_goods)\s*=\s*\{[^}]*\}", "", mod_body)
        icon_match = re.search(r'icon\s*=\s*"([^"]+)"', mod_body)
        if not icon_match:
            raise ValueError("Missing icon for " + key)
        original_icon = icon_match[1]
        icon_source = MOD / original_icon if (MOD / original_icon).is_file() else GAME / original_icon
        zip_icon = "gfx/interface/icons/ships/zip_bomb/" + zip_key + ".dds"
        icon_target = MOD / zip_icon
        icon_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(icon_source, icon_target)
        mod_body = mod_body.replace(original_icon, zip_icon)
        zip_modifications[zip_key] = mod_body
        body = re.sub(r"\b" + re.escape(key) + r"\b", zip_key, body)
    # Avoid relying on implicit modification-level selection for custom IDs.
    defaults = []
    for slot, contents in re.findall(r"(ship_mod_slot_\w+)\s*=\s*\{([^}]+)\}", body):
        options = re.findall(r"\bpdxrp_zip_\w+", contents)
        selected = next((option for option in options if option.endswith("_medium")), options[0])
        defaults.append("        " + slot + " = " + selected)
    body += "\n    default_modifications = {\n" + "\n".join(defaults) + "\n    }\n"
    navy.append(target + " = {" + body + "}")
write("common/ship_types/pdxrp_zip_bomb.txt", "\n\n".join(navy))
write("common/ship_modifications/pdxrp_zip_bomb.txt", "\n\n".join(key + " = {" + value + "}" for key, value in sorted(zip_modifications.items())))

gm = (MOD / "common/decisions/GM_decision.txt").read_text(encoding="utf-8-sig")
gm_effect = block(block(gm, "GM_spy_the_world"), "\twhen_taken")
write("common/scripted_effects/pdxrp_zip_bomb.txt", "pdxrp_zip_bomb_world_interests_effect = {" + gm_effect + "}\n")
write("common/scripted_effects/pdxrp_zip_bomb_army.txt", """
# Country scope: shared by the spawn and the existing-save deployment decision.
pdxrp_zip_bomb_create_army_effect = {
    if = {
        limit = { NOT = { has_variable = pdxrp_zip_bomb_army_deployed } }
        add_technology_researched = pdxrp_zip_bomb_virtual_arsenal
        create_military_formation = {
            name = pdxrp_zip_bomb_binary_army
            type = army
            hq_region = sr:region_east_africa
            supply_hub = s:STATE_UGANDA
            combat_unit = {
                type = unit_type:combat_unit_type_zip_binary_troopers
                state_region = s:STATE_UGANDA
                count = 500
            }
            combat_unit = {
                type = unit_type:combat_unit_type_zip_file_corruptors
                state_region = s:STATE_UGANDA
                count = 250
            }
            combat_unit = {
                type = unit_type:combat_unit_type_zip_katla_cultist_magi
                state_region = s:STATE_UGANDA
                count = 250
            }
        }
        s:STATE_UGANDA.region_state:ZIP = {
            # Unit creation recruits through barracks. Set their minimum level
            # afterwards so this does not add another 1,000 levels on top.
            create_building = { building = building_barrack level = 1000 }
        }
        set_variable = pdxrp_zip_bomb_army_deployed
    }
}
""")

# Enumerate effective technology IDs and copy Britain's current researched techs.
# This also handles spawning later in a campaign, rather than just the 1836 setup.
techs = set()
for directory in [GAME / "common/technology/technologies", MOD / "common/technology/technologies"]:
    for file in directory.glob("*.txt"):
        techs.update(re.findall(r"(?m)^(?:(?:REPLACE|REPLACE_OR_CREATE):)?([A-Za-z0-9_]+)\s*=\s*\{", file.read_text(encoding="utf-8-sig")))
techs.discard("pdxrp_zip_bomb_virtual_arsenal")
copy_techs = "\n".join(
    "    if = { limit = { c:GBR = { has_technology_researched = " + tech + " } } add_technology_researched = " + tech + " }"
    for tech in sorted(techs)
)
write("common/scripted_effects/pdxrp_zip_bomb_technologies.txt", "pdxrp_zip_bomb_copy_british_techs_effect = {\n" + copy_techs + "\n}")

# remove_building operates in state scope and takes a building type key.
# Company headquarters are generated building types, so include those too.
building_types = set()
for root in [GAME, MOD]:
    for file in (root / "common/buildings").glob("*.txt"):
        building_types.update(re.findall(r"(?m)^(?:(?:REPLACE|REPLACE_OR_CREATE):)?(building_\w+)\s*=\s*\{", file.read_text(encoding="utf-8-sig")))
    for file in (root / "common/company_types").glob("*.txt"):
        company_types = re.findall(r"(?m)^(?:(?:REPLACE|REPLACE_OR_CREATE):)?(company_\w+)\s*=\s*\{", file.read_text(encoding="utf-8-sig"))
        building_types.update("building_" + company for company in company_types)
write("common/scripted_effects/pdxrp_zip_bomb_clear_buildings.txt", "pdxrp_zip_bomb_clear_buildings_effect = {\n" + "\n".join("    remove_building = " + key for key in sorted(building_types)) + "\n}")

write("common/decisions/pdxrp_zip_bomb.txt", """
pdxrp_spawn_zip_bomb = {
    is_shown = {
        c:MOA ?= THIS
        NOT = { exists = c:ZIP }
        NOT = { has_global_variable = pdxrp_zip_bomb_spawned }
    }
    possible = { exists = c:GBR }
    when_taken = {
        # Save an actual state rather than using the state-region as a country seed.
        s:STATE_UGANDA = {
            # Clear every original state fragment before ownership changes.
            every_scope_state = { pdxrp_zip_bomb_clear_buildings_effect = yes }
            random_scope_state = { save_scope_as = pdxrp_zip_bomb_seed }
        }
        create_country = {
            tag = ZIP
            origin = c:GBR
            state = scope:pdxrp_zip_bomb_seed
            on_created = {
                set_country_type = recognized
                remove_primary_culture = cu:british
                remove_primary_culture = cu:scottish
                add_primary_culture = cu:baganda
                set_state_religion = rel:gnu_linux
                pdxrp_zip_bomb_copy_british_techs_effect = yes
                add_technology_researched = pdxrp_zip_bomb_virtual_arsenal
                activate_law = law_type:law_cooperative_ownership
                activate_law = law_type:law_council_republic
                activate_law = law_type:law_anarchy
                activate_law = law_type:law_multicultural
                activate_law = law_type:law_mass_conscription
                activate_law = law_type:law_closed_borders
                activate_law = law_type:law_isolationism
                add_modifier = { name = pdxrp_zip_bomb_collective }
            }
        }
        s:STATE_UGANDA = {
            every_scope_state = {
                set_state_owner = c:ZIP
            }
            add_homeland = cu:baganda
        }
        s:STATE_UGANDA.region_state:ZIP = {
            set_state_type = incorporated
            # Reset only after all the transferred state fragments have merged.
            kill_population_percent_in_state = { percent = 1 }
            create_pop = { culture = baganda religion = gnu_linux size = 10000000 }
        }
        c:ZIP = { pdxrp_zip_bomb_create_army_effect = yes }
        set_global_variable = pdxrp_zip_bomb_spawned
    }
    ai_chance = { value = 0 }
}

pdxrp_zip_bomb_spy_the_world = {
    is_shown = { c:ZIP ?= THIS }
    possible = { always = yes }
    when_taken = { pdxrp_zip_bomb_world_interests_effect = yes }
    ai_chance = { value = 0 }
}

pdxrp_zip_bomb_generate_money = {
    is_shown = { c:ZIP ?= THIS }
    possible = { always = yes }
    when_taken = { add_treasury = 10000000 }
    ai_chance = { value = 0 }
}

pdxrp_zip_bomb_deploy_army = {
    is_shown = {
        OR = { c:ZIP ?= THIS c:MOA ?= THIS }
        exists = c:ZIP
        c:ZIP = { NOT = { has_variable = pdxrp_zip_bomb_army_deployed } }
    }
    possible = { s:STATE_UGANDA.region_state:ZIP = { owner = c:ZIP } }
    when_taken = { c:ZIP = { pdxrp_zip_bomb_create_army_effect = yes } }
    ai_chance = { value = 0 }
}

pdxrp_zip_bomb_adopt_gnu_linux = {
    is_shown = {
        OR = { c:ZIP ?= THIS c:MOA ?= THIS }
        exists = c:ZIP
        c:ZIP = { NOT = { country_has_state_religion = rel:gnu_linux } }
    }
    possible = { always = yes }
    when_taken = { c:ZIP = { set_state_religion = rel:gnu_linux } }
    ai_chance = { value = 0 }
}

pdxrp_zip_bomb_seed_pops_culture = {
    is_shown = { c:ZIP ?= THIS }
    possible = {
        any_scope_state = {
            culture_percent_state = { target = cu:baganda value < 0.01 }
        }
    }
    when_taken = {
        every_scope_state = {
            limit = { culture_percent_state = { target = cu:baganda value < 0.01 } }
            every_scope_pop = {
                limit = { NOT = { culture = cu:baganda } }
                change_pop_culture = { target = cu:baganda value = 0.02 }
            }
        }
    }
    ai_chance = { value = 0 }
}

pdxrp_zip_bomb_nerve_stapling = {
    is_shown = { c:ZIP ?= THIS }
    possible = { always = yes }
    when_taken = {
        add_radicals = { value = -0.10 }
    }
    ai_chance = { value = 0 }
}
""")

write("common/coat_of_arms/coat_of_arms/pdxrp_zip_bomb.txt", """
ZIP = {
    pattern = "pattern_solid.tga"
    color1 = "grey"
    textured_emblem = {
        texture = "te_zip_bomb_winrar.dds"
        instance = { position = { 0.5 0.5 } scale = { 0.66 1.0 } }
    }
}
""")
write("common/flag_definitions/pdxrp_zip_bomb.txt", """
ZIP = {
    flag_definition = {
        coa = ZIP
        # The DEFAULT Anarchy flag has priority 2,000.
        priority = 10000
        allow_revolutionary_indicator = no
    }
}
""")
texture = MOD / "gfx/coat_of_arms/textured_emblems/te_zip_bomb_winrar.dds"
texture.parent.mkdir(parents=True, exist_ok=True)
Image.open(MOD / "tools/assets/zip_bomb_winrar.png").convert("RGBA").save(texture, pixel_format="DXT5")

# Vanilla culture keys need explicit override localization to take precedence.
write("localization/english/replace/pdxrp_zip_bomb_culture_l_english.yml", '''
l_english:
 baganda:0 "Pops"
 PLURAL_DEMONYM_baganda:0 "Pops"
 SINGULAR_DEMONYM_baganda:0 "Pop"
 PLURAL_DEMONYM_FEMALE_baganda:0 "Pops"
 SINGULAR_DEMONYM_FEMALE_baganda:0 "Pop"
''', localization=True)

write("localization/english/pdxrp_zip_bomb_l_english.yml", '''
l_english:
 ZIP:0 "ZIP Bomb"
 ZIP_ADJ:0 "ZIP Bomb"
 pdxrp_pop_character_name:0 "Part of Population"
 pdxrp_pop_empty_surname:0 ""
 building_zip_data_center:0 "Data Center"
 building_zip_data_center_desc:0 "Produces food and supplies for ZIP Bomb."
 bg_zip_data_centers:0 "Data Centers"
 pmg_zip_data_center:0 "Virtual Production"
 pm_zip_data_center:0 "Materialize Resources"
 gnu_linux:0 "GNU/Linux"
 heritage_virtual:0 "Virtual"
 heritage_group_virtual:0 "Virtual"
 language_assembly:0 "Assembly"
 language_group_assembly:0 "Assembly"
 pdxrp_spawn_zip_bomb:0 "Extract ZIP Bomb in Uganda"
 pdxrp_spawn_zip_bomb_desc:0 "They are coming"
 pdxrp_zip_bomb_spy_the_world:0 "ZIP Bomb: Spy on the World"
 pdxrp_zip_bomb_spy_the_world_desc:0 "Keep an eye on the whole world."
 pdxrp_zip_bomb_generate_money:0 "ZIP Bomb: Generate Money"
 pdxrp_zip_bomb_generate_money_desc:0 "Add £10,000,000 to the treasury."
 pdxrp_zip_bomb_collective:0 "Didn't click anything during hotjoin"
 pdxrp_zip_bomb_adopt_gnu_linux:0 "ZIP Bomb: Adopt GNU/Linux"
 pdxrp_zip_bomb_adopt_gnu_linux_desc:0 "Make GNU/Linux the state religion."
 pdxrp_zip_bomb_seed_pops_culture:0 "ZIP Bomb: Seed Pops Culture"
 pdxrp_zip_bomb_seed_pops_culture_desc:0 "Turn 2% of other cultures into Pops in states with less than 1% Pops."
 pdxrp_zip_bomb_nerve_stapling:0 "Nerve Stapling"
 pdxrp_zip_bomb_nerve_stapling_desc:0 "Please don't go. The Drones need you. They look up to you"
 pdxrp_zip_bomb_binary_army:0 "Binary Army"
 pdxrp_zip_bomb_deploy_army:0 "ZIP Bomb: Deploy the Binary Army"
 pdxrp_zip_bomb_deploy_army_desc:0 "Raise the Binary Army in Uganda."
 pdxrp_zip_bomb_virtual_arsenal:0 "Virtual Arsenal"
 pdxrp_zip_bomb_virtual_arsenal_desc:0 "Unlock ZIP Bomb's army and navy."
 combat_unit_type_zip_binary_troopers:0 "Binary Troopers"
 combat_unit_type_zip_file_corruptors:0 "File Corruptors"
 combat_unit_type_zip_katla_cultist_magi:0 "Katla Cultist Magi"
 ship_type_zip_linux_ship:0 "Linux Ships"
 ship_type_zip_linux_ship_desc:0 "A super dreadnought that runs on grain."
 ship_type_zip_dragon_carrier:0 "Dragon Carriers"
 ship_type_zip_dragon_carrier_desc:0 "An aircraft carrier that runs on grain."
''', localization=True)
write("localization/english/pdxrp_zip_bomb_ship_modifications_l_english.yml", "l_english:\n" + "\n".join(" " + key + ':0 "$' + key.removeprefix("pdxrp_zip_") + '$"' for key in sorted(zip_modifications)), localization=True)
print("Built ZIP Bomb: country, culture, decisions, modifiers, units, ships and flag.")
