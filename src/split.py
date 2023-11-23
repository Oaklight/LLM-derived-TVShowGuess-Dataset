import json
import os

origin_dir = "./merge_split_ready/merged"
tgt_dir = "./merge_split_ready/splitted"
os.makedirs(origin_dir, exist_ok=True)
os.makedirs(tgt_dir, exist_ok=True)

show_seq = ("FRIENDS", "The_Big_Bang_Theory", "Frasier", "Gilmore_Girls", "The_Office")
test_season_dict = {
    "FRIENDS": 9,
    "The_Big_Bang_Theory": 8,
    "Frasier": 10,
    "Gilmore_Girls": 5,
    "The_Office": 8,
}


def write_json(tgt_dir, show_name, scene_list, split):
    tgt_scene_path = os.path.join(tgt_dir, f"{show_name}.{split}.json")
    with open(tgt_scene_path, "w") as f:
        for e in scene_list:
            f.write(json.dumps(e, sort_keys=True) + "\n")

if __name__ == "__main__":
    for show_name in show_seq:
        origin_scene_path = os.path.join(origin_dir, f"{show_name}.json")

        with open(origin_scene_path, "r") as f:
            # read as jsonl, each row is a json entry
            scene_list = [json.loads(line) for line in f]

        scenes_train = []
        scenes_dev = []
        scenes_test = []

        for scene in scene_list:
            if scene["season_id"] < test_season_dict[show_name]:
                scenes_train.append(scene)
            else:
                scenes_dev.append(scene)

        half_idx = len(scenes_dev) // 2
        scenes_test = scenes_dev[half_idx:]
        scenes_dev = scenes_dev[:half_idx]

        write_json(tgt_dir, show_name, scenes_train, "train")
        write_json(tgt_dir, show_name, scenes_dev, "dev")
        write_json(tgt_dir, show_name, scenes_test, "test")
