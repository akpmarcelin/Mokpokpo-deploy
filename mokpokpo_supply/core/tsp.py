def solve_tsp(dist_matrix):
    n = len(dist_matrix)
    visited = [False] * n
    order = [0]
    visited[0] = True

    for _ in range(n - 1):
        last = order[-1]
        next_city = None
        best_dist = float('inf')
        for j in range(n):
            if not visited[j] and dist_matrix[last][j] < best_dist:
                best_dist = dist_matrix[last][j]
                next_city = j
        visited[next_city] = True
        order.append(next_city)

    # Retourner à l'entrepôt (optionnel)

    return order

