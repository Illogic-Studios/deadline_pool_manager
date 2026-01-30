def weighted_snake_draft_distribution(workers_scores, pool_percentages):
        worker_nb_per_pool = {}
        total_workers = len(workers_scores)
        total_percentages = 100.0
        for pool_name, percentage in pool_percentages:
            worker_nb = round(total_workers * percentage / total_percentages) if total_percentages > 0 else 0
            worker_nb_per_pool[pool_name] = worker_nb
            total_workers -= worker_nb
            total_percentages -= percentage

        worker_assignement_order = {}
        scores = workers_scores.copy()
        pools = [pool_name for pool_name, _ in pool_percentages]
        pool_nb = len(pool_percentages)
        while scores:
            for i in range(pool_nb):
                if i < len(scores):
                    worker_assignement_order[scores.pop(0)[0]] = pools.copy()
                else:
                    break
            for i in range(pool_nb):
                if i < len(scores):
                    worker_assignement_order[scores.pop(-1)[0]] = pools.copy()
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

        for _, pools in worker_assignement_order.items():
            assigned_pool = pool_order.pop(0)
            pools.remove(assigned_pool)
            pools.insert(0, assigned_pool)

        return worker_assignement_order

        # workers_assignments = {worker: pool_percentages.keys() for worker in worker_nb_per_pool.values()}
        # for i in range(len(worker_order)):
        #     pool_name = pool_order[i]
        #     worker_name = worker_order[i]
        #     workers_assignments[worker_name].remove(pool_name)
        #     workers_assignments[worker_name].insert(0, pool_name)

        # return workers_assignments

if __name__ == "__main__":
    # Exemple d'utilisation
    workers_scores = [
        ("worker1", 95),
        ("worker2", 85),
        ("worker3", 75),
        ("worker4", 65),
        ("worker5", 55),
        ("worker6", 45),
        ("worker7", 35),
        ("worker8", 25),
        ("worker9", 15),
        ("worker10", 5),
    ]


    pool_percentages = [
        ("poolA", 40),
        ("poolB", 30),
        ("poolC", 20),
        ("poolD", 10),
    ]

    distribution = weighted_snake_draft_distribution(workers_scores, pool_percentages)

    for worker, pools in distribution.items():
        print(f"{worker}: {pools}")
    