def weighted_snake_draft_distribution(workers_scores, pool_percentages):
        worker_nb_per_pool = {}
        total_workers = len(workers_scores)
        total_percentages = 0.0
        for pool_name, percentage in pool_percentages.items():
            worker_nb = total_workers * percentage / (100.0 - total_percentages)
            worker_nb = 1 if worker_nb < 1.0 else round(worker_nb)
            worker_nb_per_pool[pool_name] = worker_nb
            total_workers -= worker_nb
            total_percentages += percentage

        worker_order = []
        scores = workers_scores.copy()
        pool_nb = len(pool_percentages)
        while scores:
            for i in range(pool_nb):
                if i < len(scores):
                    worker_order.append(scores.pop(0))
                else:
                    break
            for i in range(pool_nb):
                if i < len(scores):
                    worker_order.append(scores.pop(-1))
                else:
                    break

        pool_order = []
        total_workers = len(workers_scores)
        while total_workers > 0:
            for pool_name in worker_nb_per_pool.keys():
                if worker_nb_per_pool[pool_name] > 0:
                    pool_order.append(pool_name)
                    worker_nb_per_pool[pool_name] -= 1
                    total_workers -= 1

        pool_assignments = {pool: [] for pool in worker_nb_per_pool.keys()}
        for i in range(len(worker_order)):
            pool_name = pool_order[i]
            worker_name = worker_order[i]
            pool_assignments[pool_name].append(worker_name)

        return pool_assignments

if __name__ == "__main__":
    # Exemple d'utilisation
    workers_scores = [
        ("worker1", {"score": 95}),
        ("worker2", {"score": 90}),
        ("worker3", {"score": 85}),
        ("worker4", {"score": 80}),
        ("worker5", {"score": 75}),
        ("worker6", {"score": 70}),
        ("worker7", {"score": 65}),
        ("worker8", {"score": 60}),
        ("worker9", {"score": 55}),
        ("worker10", {"score": 50}),
        ("worker11", {"score": 45}),
        ("worker12", {"score": 40}),
    ]


    pool_percentages = {
        "poolA": 80,
        "poolB": 10,
        "poolC": 10,
        "poolD": 1,
    }

    distribution = weighted_snake_draft_distribution(workers_scores, pool_percentages)

    # Calculer et afficher le score total par pool
    # workers_scores contient des tuples (worker_name, {"score": value})
    score_by_worker = {name: info.get("score", 0) for name, info in workers_scores}

    total_score_per_pool = {}
    distribution_names = {}
    for pool_name, workers in distribution.items():
        total = 0
        names = []
        for worker in workers:
            # worker peut être soit un nom (str), soit un tuple (name, info)
            if isinstance(worker, tuple) and len(worker) > 0:
                wname = worker[0]
            else:
                wname = worker
            names.append(wname)
            total += score_by_worker.get(wname, 0)
        distribution_names[pool_name] = names
        total_score_per_pool[pool_name] = total

    print("Distribution par pool:")
    for pool_name, names in distribution_names.items():
        print(f"  {pool_name}: {names}")

    print("\nScore total par pool:")
    for pool_name, total in total_score_per_pool.items():
        print(f"  {pool_name}: {total}")
    