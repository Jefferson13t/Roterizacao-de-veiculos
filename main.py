import pyomo.environ as pyo
import matplotlib.pyplot as plt
from pyomo.opt import SolverFactory
from matplotlib.patches import Circle
import random


def solve(
        N: list[int],
        C: list[float],
        d: dict[int, float],
        c: dict[tuple[int, int], float],
        K: list[int],
        Q: float, 
    ) :
    """
        args
            N: conjunto de Nós (deposito = 0 = n + 1)
            C: conjunto de nós que são clientes
            d: demanda por cliente
            E: conjunto de Arestas
            c: custo da aresta
            K: conjunto de veículos
            Q: capacidade veículos
    """

    opt = SolverFactory('highs')

    model = pyo.ConcreteModel()

    # Conjunto de arcos
    E = [
        (i, j)
        for i in N
        for j in N
        if i != j
    ]



    model.u = pyo.Var(K, C, within=pyo.NonNegativeReals)
    model.x = pyo.Var(E, K, within=pyo.Binary)

    def fo(model):
        return pyo.quicksum(
            c[(i, j)] * model.x[i, j, k]
            for (i, j) in E
            for k in K
        )

    model.o = pyo.Objective(
        rule=fo,
        sense=pyo.minimize
    )

    # Restrições

    model.c = pyo.ConstraintList()

    for k in K:
        for i in N:
            for j in N:
                if i not in C:
                    continue
                if j not in C:
                    continue
                if j == i:
                    continue

                model.c.add(
                    model.u[k, j] - model.u[k, i] >= d[j] - Q * (1 - model.x[i, j, k])
                )

    for k in K:
        for i in N:
            if i not in C:
                continue
   
            model.c.add(model.u[k, i] >= d[i])
            model.c.add(model.u[k, i] <= Q)



    for i in C:
        model.c.add(
            pyo.quicksum(
                model.x[i, j, k]
                for j in N
                if j != i
                for k in K
            ) == 1
        )

    # for k in K:
    #     model.c.add(
    #         pyo.quicksum(
    #             d[i] * model.x[i, j, k]
    #             for i in C
    #             for j in N
    #             if j != i
    #         ) <= Q
    #     )

    for k in K:
        model.c.add(
            pyo.quicksum(
                model.x[0, j, k]
                for j in C
                if j != 0
            ) <= 1
        )


    for k in K:
        for h in C:
            model.c.add(
                pyo.quicksum(
                    model.x[i, h, k]
                    for i in N
                    if h != i
                ) - pyo.quicksum(
                    model.x[h, j, k]
                    for j in N
                    if j != h
                ) == 0
            )

    for k in K:
        model.c.add(
            pyo.quicksum(
                model.x[i, 0, k]
                for i in C
                if i != 0
            ) == 1
        )

    # Resolver
    result = opt.solve(model, tee=False)

    caminho_por_carro = {}

    for k in K:
        caminho_veiculo_k = []

        for (i, j) in E:
            if pyo.value(model.x[i, j, k]) > 0.5:

                caminho_veiculo_k.append((i, j))

        caminho_por_carro[k] = caminho_veiculo_k

    return caminho_por_carro


def draw_graph(nos: list[tuple[int, int]], clientes: list[int], caminho_por_veiculo: list[list[tuple[tuple[int, int], tuple[int, int]]]]) -> None:

    fig, ax = plt.subplots()


    ALTURA = 50
    LARGURA = 100

    for i, no in enumerate(nos):

        cor = "#050005"

        raio = 1

        if i == 0:
            cor = "#0400FF"

        if i in clientes:
            raio = 2

        no = Circle(
            no,  # posição
            raio,    # largura e altura
            facecolor=cor,
            edgecolor="#ffffff00"
        )
        ax.add_patch(no)


    for arestas in caminho_por_veiculo:

        cores = [
            "#FF0000",  # vermelho
            "#00FF00",  # verde
            "#0000FF",  # azul
            "#FFFF00",  # amarelo
            "#FF00FF",  # magenta
            "#00FFFF",  # ciano
            "#FFA500",  # laranja
            "#800080",  # roxo
            "#FFC0CB",  # rosa
            "#A52A2A",  # marrom
            "#008000",  # verde escuro
            "#000080",  # azul marinho
            "#808000",  # oliva
            "#800000",  # vinho
            "#008080",  # teal
            "#4B0082",  # índigo
            "#EE82EE",  # violeta
            "#FFD700",  # dourado
            "#808080",  # cinza
            "#000000",  # preto
        ]

        for i, aresta in enumerate(arestas):

            no_inicio = aresta[0]
            no_fim = aresta[1]

            plt.annotate(
                "",
                xy=no_inicio,  # Ponto onde fica a ponta da seta
                xytext=no_fim,  # Ponto onde começa a cauda (e fica o texto)
                arrowprops=dict(
                    facecolor=cores[i],
                    edgecolor="none",
                    shrink=0.05,
                    width=2,
                    headwidth=10
                ),
            )



    ax.set_xlim(0, LARGURA)
    ax.set_ylim(0, ALTURA)
    ax.set_aspect("equal")


    plt.show()


def main() -> None:

    quantidade_nos = 6
    quantidade_veiculos = 2

    # Nós: 0 = depósito
    #      1, 2, 3, 4, 5 = clientes
    N = list(range(quantidade_nos))
    K = list(range(quantidade_veiculos))

    C = [1.0, 2, 3, 4, 5]

    # Demanda dos clientes
    d = {
        1: 4,
        2: 3.0,
        3: 5,
        4: 2,
        5: 4,
    }

    # Capacidade dos veículos
    Q = 10

    posicao = [
        (random.randint(0, 100), random.randint(0, 50))
        for i in N
    ]

    def calc_dist(posicao_i: tuple[int, int], posicao_j: tuple[int, int]) -> float:
        x_i = posicao_i[0]
        y_i = posicao_i[1]

        x_j = posicao_j[0]
        y_j = posicao_j[1]
    
        return (x_j - x_i) ** 2 + (y_j - y_i) ** 2
        

    c = {
        (i, j): calc_dist(posicao[i], posicao[j])
        for i in N
        for j in N
    }


    resultado = solve(N, C, d, c, K, Q)


    caminho_por_veiculo = []

    for k in K:
        caminho = []

        for aresta in resultado[k]:
            pos_i = posicao[aresta[0]]
            pos_j = posicao[aresta[1]]

            caminho.append((pos_i, pos_j))

        caminho_por_veiculo.append(caminho)


    draw_graph(posicao, C,  caminho_por_veiculo) 


if __name__ == "__main__":
    main()

