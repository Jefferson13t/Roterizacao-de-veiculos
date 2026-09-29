import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

import matplotlib.pyplot as plt
from pyomo.opt import SolverFactory
from matplotlib.patches import Circle
import random


def solve(
        C: list[float],
        d: list[float],
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
        for i in range(len(C))
        for j in range(len(C))
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

    # Restrição da formulação Miller-Tucker-Zemlin Formulation
    for k in K:
        n = len(C)

        for i in range(1, len(C)):
            for j in range(1, len(C)):
                if j == i:
                    continue

                model.c.add(
                    model.u[k, j] - model.u[k, i] >= d[i] - Q * (1 - model.x[i, j, k])
                )

    for k in K:
        for i in range(1, len(C)):
 
            model.c.add(d[i] <= model.u[k, i])
            model.c.add(model.u[k, i] <= Q)

    # Cada cliente é atendido por somente um veículo
    for i in range(1, len(C)):
        model.c.add(
            pyo.quicksum(
                model.x[i, j, k]
                for j in range(len(C))
                if j != i
                for k in K
            ) == 1
        )

    # Os clientes atendidos por um veículo devem respeitar a capacidade
    for k in K:
        model.c.add(
            pyo.quicksum(
                d[i] * model.x[i, j, k]
                for i in range(len(C))
                for j in range(len(C))
                if j != i
            ) <= Q
        )

    # As próximas 3 restrições são restrições de fluxo em rede

    # Todos os veículos devem sair do depósito. (Primeiro vertice)
    for k in K:
        model.c.add(
            pyo.quicksum(
                model.x[0, j, k]
                for j in range(len(C))
                if j != 0
            ) == 1
        )

    # Somatorio dos veículos entrando em um vertice deve ser igual ao somatorio dos veículos saindo. (Não tem acumulo)
    for k in K:
        for h in range(len(C)):
            model.c.add(
                pyo.quicksum(
                    model.x[i, h, k]
                    for i in range(len(C))
                    if h != i
                ) - pyo.quicksum(
                    model.x[h, j, k]
                    for j in range(len(C))
                    if j != h
                ) == 0
            )

    # Todos os veículos devem terminar no depósito
    for k in K:
        model.c.add(
            pyo.quicksum(
                model.x[i, 0, k]
                for i in range(len(C))
                if i != 0
            ) == 1
        )

    # Resolver
    results = opt.solve(model, tee=False)

    # model.load(results)

    # if(results.solver.termination_condition == TerminationCondition.noSolution):
    #     print("Infeasible")
    #     print(results)

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


    for i, arestas in enumerate(caminho_por_veiculo):

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

        path_color = cores[i]

        for aresta in arestas:

            no_inicio = aresta[0]
            no_fim = aresta[1]

            plt.annotate(
                "",
                xy=no_inicio,  # Ponto onde fica a ponta da seta
                xytext=no_fim,  # Ponto onde começa a cauda (e fica o texto)
                arrowprops=dict(
                    facecolor=path_color,
                    edgecolor="none",
                    shrink=0.05,
                    width=2,
                    headwidth=10
                ),
            )



    ax.set_xlim(0, LARGURA)
    ax.set_ylim(0, ALTURA)
    ax.set_aspect("equal")

    output_img_path = 'outputs/solution.png'

    plt.savefig(
        output_img_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()


def main() -> None:

    quantidade_veiculos = 3
    quantidade_clientes = 15

    K = list(range(quantidade_veiculos))

    # Clientes
    C = [i for i in range(quantidade_clientes)]

    # Demanda dos clientes
    d = [0.0] + [round(random.uniform(1.0, 5.0), 1) for _ in range(quantidade_clientes)]

    # Capacidade dos veículos
    Q = 20

    posicao = [
        (random.randint(0, 100), random.randint(0, 50))
        for _ in range(quantidade_clientes)
    ]

    def calc_dist(posicao_i: tuple[float, float], posicao_j: tuple[float, float]) -> float:
        x_i = posicao_i[0]
        y_i = posicao_i[1]

        x_j = posicao_j[0]
        y_j = posicao_j[1]
    
        return (x_j - x_i) ** 2 + (y_j - y_i) ** 2
        

    c = {
        (i, j): calc_dist(posicao[i], posicao[j])
        for i in range(len(C))
        for j in range(len(C))
    }

    resultado = solve(C, d, c, K, Q)


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

