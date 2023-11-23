# Scenes in the five shows are ordered.
# The id of scenes are accumulated, within and across shows. Within each show,
# the earlier scene split in earlier episode has smaller id. Across shows, we
# follow this order: FRIENDS, The Big Bang Theory, Frasier, Gilmore Girls, The Office

import json
import os

origin_dir = "./tvsg_original/merged"
tgt_dir = "./merge_split_ready/merged"
plot_summ_dir = "./plot_summ_files"
heuristic_len = 100

scene_id = 1
scene_cnts = []
scene_start_ids = []
show_seq = ("FRIENDS", "The_Big_Bang_Theory", "Frasier", "Gilmore_Girls", "The_Office")


# dict_keys(['id', 'title', 'lines', 'participants', 'episode_id'])
def reorganize_scene_entry(scene, idx):
    scene["scene_id"] = idx
    scene["season_id"] = int(scene["episode_id"].split("x")[0])
    new_lines, answers_dict = mask_speakers(scene["lines"])
    scene["answers"] = answers_dict
    scene["scene_current"] = new_lines

    return scene


def mask_speakers(lines):
    answers_dict = {}  # for P{x} to name mapping
    answers = []  # for fixed seq
    new_lines = []
    for line in lines:
        who_true, words = line[0], line[1]

        who_masked = who_true
        # skip background
        if who_true != "background":
            # mask out whoever speaking in this line
            if who_true not in answers:
                who_masked = f"P{len(answers)}"
                answers.append(who_true)
                answers_dict[who_masked] = who_true
            else:
                who_masked = f"P{answers.index(who_true)}"

        idx = words.find(":")
        words = who_masked + " : " + words[idx + 1 :]
        new_lines.append([who_true, words])

    return new_lines, answers_dict


def add_prev_one(scene_curr, scene_prev):
    if scene_prev is not None:
        scene_curr["scene_prev_one"] = scene_prev["lines"]
    else:
        scene_curr["scene_prev_one"] = []

    return scene_curr


def get_background_plots(scene_details, summary_dict, plot_summ_len):
    scene_ids = list(summary_dict.keys())
    tgt = scene_details["scene_id"]
    if tgt not in scene_ids:
        print(f"[{tgt}] missing")
        return "", []
    idx = scene_ids.index(tgt)

    summary_words = []
    used_idx = []

    # find matched scene from behind but add it to the front
    for prev_idx in range(idx - 1, -1, -1):
        current_line = summary_dict[scene_ids[prev_idx]].split()
        if len(summary_words) + len(current_line) < plot_summ_len:
            summary_words = current_line + summary_words
            used_idx.append(scene_ids[prev_idx])
        else:
            break

    background = " ".join(summary_words)
    return background, used_idx


def add_plot_summ(scene, summary_dict, heuristic_len=100):
    plot_summ_merged, used_idx = get_background_plots(
        scene, summary_dict, heuristic_len
    )
    scene["heuristic_len"] = heuristic_len
    scene["scene_prev_many_summ"] = plot_summ_merged
    scene["scene_prev_many_idx"] = used_idx

    return scene


def add_prev_many(scene, all_scenes_dict):
    lines_merged = []
    for idx in sorted(scene["scene_prev_many_idx"]):
        lines_merged.extend(all_scenes_dict[idx]["lines"])
    scene["scene_prev_many"] = lines_merged

    return scene


def cleanup_scene_entry(scene):

    del scene["id"]
    del scene["participants"]
    del scene["lines"]

    return scene


if __name__ == "__main__":
    # get file names in origin_dir
    for show_name in show_seq:
        origin_scene_path = os.path.join(origin_dir, f"{show_name}.merged.json")
        processed_scene_path = os.path.join(tgt_dir, f"{show_name}.json")
        plot_summ_path = os.path.join(
            plot_summ_dir, f"plot_summ.{show_name}.merged.json"
        )

        with open(origin_scene_path, "r") as f:
            # read as jsonl, each row is a json entry
            scene_list = [json.loads(line) for line in f]
        with open(plot_summ_path, "r") as f:
            data = json.load(f)
            plotsumm_dict = {int(k) if k.isdigit() else k: v for k, v in data.items()}
            # sort plotsumm_dict by key
            plotsumm_dict = dict(sorted(plotsumm_dict.items(), key=lambda x: x[0]))

        scene_start_ids.append(sum(scene_cnts) + 1)
        scene_cnts.append(len(scene_list))

        scene_list = list(
            map(
                lambda s0, s1: add_prev_one(s0, s1),
                scene_list,
                [None] + scene_list[:-1],
            )
        )

        scene_list = list(
            map(
                lambda e, i: reorganize_scene_entry(e, i + scene_start_ids[-1]),
                scene_list,
                range(len(scene_list)),
            )
        )

        scene_list = list(
            map(lambda e: add_plot_summ(e, plotsumm_dict, heuristic_len), scene_list)
        )

        all_scenes_dict = {e["scene_id"]: e for e in scene_list}
        scene_list = list(map(lambda e: add_prev_many(e, all_scenes_dict), scene_list))

        scene_list = list(map(lambda e: cleanup_scene_entry((e)), scene_list))

        with open(processed_scene_path, "w") as f:
            for e in scene_list:
                f.write(json.dumps(e, sort_keys=True) + "\n")
