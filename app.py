from flask import Flask, render_template, request, jsonify
import random
import math

app = Flask(__name__)


BUS_LINES = [
    {"id": "101", "name": "101 - Rodoviária / Asa Norte",   "color": "#FF6B35"},
    {"id": "383", "name": "383 - Ceilândia / Rodoviária",     "color": "#4ECDC4"},
    {"id": "320", "name": "320 - Samambaia / W3 Sul",         "color": "#45B7D1"},
    {"id": "350", "name": "350 - Taguatinga / Eixo Monumental","color": "#96CEB4"},
    {"id": "502", "name": "502 - Gama / Rodoviária",        "color": "#FFEAA7"},
    {"id": "615", "name": "615 - Sobradinho / Rodoviária",    "color": "#DDA0DD"},
    {"id": "710", "name": "710 - Recanto das Emas / W3",      "color": "#F0A500"},
    {"id": "825", "name": "825 - São Sebastião / Centro",     "color": "#98D8C8"},
]


def median_of_medians(arr, k=None):
    steps = []
    arr = list(arr)

    if k is None:
        k = (len(arr) - 1) // 2  # indice da mediana

    def _select(lst, rank):
        if len(lst) <= 5:
            s = sorted(lst)
            steps.append({
                "type": "base_case",
                "group": lst,
                "sorted": s,
                "chosen": s[rank]
            })
            return s[rank]

        # Dividir em grupos de 5
        groups = [lst[i:i+5] for i in range(0, len(lst), 5)]
        steps.append({
            "type": "split_groups",
            "groups": [g for g in groups]
        })

        # Mediana de cada grupo
        medians = []
        for g in groups:
            sg = sorted(g)
            med = sg[len(sg) // 2]
            medians.append(med)

        steps.append({
            "type": "group_medians",
            "medians": medians
        })

        # Mediana das medianas (recursao)
        pivot = _select(medians, (len(medians) - 1) // 2)
        steps.append({"type": "pivot_chosen", "pivot": pivot})

        # Particionar
        low  = [x for x in lst if x < pivot]
        high = [x for x in lst if x > pivot]
        k_low = len(low)

        steps.append({
            "type": "partition",
            "pivot": pivot,
            "low": low,
            "high": high
        })

        if rank < k_low:
            return _select(low, rank)
        elif rank == k_low:
            return pivot
        else:
            return _select(high, rank - k_low - 1)

    result = _select(arr, k)
    return result, steps


def generate_scenario(chaos_level=0.5):
    n = random.randint(5, 8)
    buses = random.sample(BUS_LINES, n)

    planned_order = [b["id"] for b in buses]
    real_order    = planned_order.copy()

    num_swaps = int(chaos_level * n * 2)
    for _ in range(num_swaps):
        i, j = random.sample(range(n), 2)
        real_order[i], real_order[j] = real_order[j], real_order[i]

    delays = []
    for bus_id in real_order:
        if chaos_level < 0.3:
            delay = random.randint(-2, 8)
        elif chaos_level < 0.7:
            delay = random.randint(-1, 20)
        else:
            delay = random.randint(5, 45)
        delays.append(delay)

    bus_map = {b["id"]: b for b in BUS_LINES}

    return {
        "planned": planned_order,
        "real":    real_order,
        "delays":  delays,
        "buses":   {b["id"]: b for b in buses},
        "chaos_level": chaos_level
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/algorithm/median", methods=["POST"])
def explain_median():
    data = request.get_json(silent=True) or {}
    arr  = data.get("array", [2, 5, 3, 40, 4, 6])
    val, steps = median_of_medians(arr)
    return jsonify({"array": arr, "median": val, "steps": steps})


if __name__ == "__main__":
    app.run(debug=True, port=5000)