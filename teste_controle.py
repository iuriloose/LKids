import pygame

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("Nenhum controle encontrado.")
    input("Pressione Enter para sair...")
    exit()

controle = pygame.joystick.Joystick(0)
controle.init()

print("Controle:", controle.get_name())
print("Botões:", controle.get_numbuttons())
print("Eixos:", controle.get_numaxes())
print("Direcionais:", controle.get_numhats())
print()
print("Mova os analógicos e aperte L2/R2.")
print("Pressione ESC para sair.")
print()

rodando = True

while rodando:

    for evento in pygame.event.get():

        if evento.type == pygame.JOYAXISMOTION:

            valor = evento.value

            if abs(valor) > 0.15:
                print(
                    "EIXO:",
                    evento.axis,
                    "VALOR:",
                    round(valor, 2)
                )

        if evento.type == pygame.JOYBUTTONDOWN:
            print("BOTÃO PRESSIONADO:", evento.button)

        if evento.type == pygame.JOYHATMOTION:
            print("DIRECIONAL:", evento.value)

        if evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_ESCAPE:
                rodando = False

pygame.quit()