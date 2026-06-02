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


def merge_count_inversions(arr):
    steps = []

    def merge_sort(a):
        if len(a) <= 1:
            return a, 0
        
        mid = len(a) // 2
        left, inv_left = merge_sort(a[:mid])
        right, inv_right = merge_sort(a[mid:])
        
        merged = []
        inversions = inv_left + inv_right
        i = j = 0
        
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                # Todos os elementos restantes em 'left' formam inversão com right[j]
                inversions += len(left) - i
                steps.append({
                    "type": "inversion",
                    "left_val": left[i],
                    "right_val": right[j],
                    "count": len(left) - i
                })
                merged.append(right[j])
                j += 1
        
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, inversions

    sorted_arr, total = merge_sort(arr)
    return total, steps


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


@app.route("/api/simulate", methods=["POST"])
def simulate():
    data        = request.get_json(silent=True) or {}
    chaos_level = float(data.get("chaos_level", 0.5))
    chaos_level = max(0.0, min(1.0, chaos_level))

    scenario = generate_scenario(chaos_level)

    # Mapear IDs da ordem real para indices da ordem planejada
    planned = scenario["planned"]
    real    = scenario["real"]
    rank_map = {bus_id: idx for idx, bus_id in enumerate(planned)}
    real_as_ranks = [rank_map[b] for b in real]

    # Contagem de Inversoes
    inversions, inv_steps = merge_count_inversions(real_as_ranks)

    # Mediana das medianas nos atrasos
    delays     = scenario["delays"]
    median_val, mom_steps = median_of_medians(delays)

    # Metricas derivadas
    max_inversions = len(planned) * (len(planned) - 1) // 2
    chaos_pct      = (inversions / max_inversions * 100) if max_inversions > 0 else 0

    if chaos_pct < 20:
        status = "OPERAÇÃO NORMAL"
        status_level = "ok"
    elif chaos_pct < 50:
        status = "ATENÇÃO NECESSÁRIA"
        status_level = "warning"
    else:
        status = "CAOS OPERACIONAL"
        status_level = "critical"

    # Inversoes por par de onibus (para visualizaçao)
    inversion_pairs = []
    for i in range(len(real)):
        for j in range(i + 1, len(real)):
            if rank_map[real[i]] > rank_map[real[j]]:
                inversion_pairs.append((real[i], real[j]))

    return jsonify({
        "scenario": scenario,
        "inversions": {
            "count":          inversions,
            "max_possible":   max_inversions,
            "chaos_percent":  round(chaos_pct, 1),
            "pairs":          inversion_pairs,
            "steps":          inv_steps[:8],
        },
        "median": {
            "value": median_val,
            "delays": delays,
            "steps": mom_steps[:10],
        },
        "status":       status,
        "status_level": status_level,
    })


@app.route("/api/algorithm/inversion", methods=["POST"])
def explain_inversion():
    data = request.get_json(silent=True) or {}
    arr  = data.get("array", [3, 1, 2, 5, 4])
    count, steps = merge_count_inversions(arr)
    return jsonify({"array": arr, "inversions": count, "steps": steps})


@app.route("/api/algorithm/median", methods=["POST"])
def explain_median():
    data = request.get_json(silent=True) or {}
    arr  = data.get("array", [2, 5, 3, 40, 4, 6])
    val, steps = median_of_medians(arr)
    return jsonify({"array": arr, "median": val, "steps": steps})


if __name__ == "__main__":
    app.run(debug=True, port=5000)