package main

// Payload EMV Pix voluntário fornecido pelo mantenedor. Não contém valor fixo,
// não cria cobrança e não requer conexão de rede nem dados do usuário.
const pixPayload = "00020126970014BR.GOV.BCB.PIX0136dd20e247-c861-44a1-9a21-2ddb827465e90235Ajude seu amiguinho a tomar um café5204000053039865802BR5925Pedro Henrique Pessoa Cru6009SAO PAULO62140510WP4lJ5p0Ib630482B0"

// QR com correção M e quiet zone de 4 módulos. Gerado localmente do
// pixPayload (61x61 bits, row-major, MSB-first). Não chamar APIs externas.
const pixQRSize = 65
const pixQRBitsBase64 = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/nxQBs+LP4BBN0iVlFiQQC66k79BRsugF1igWAilpdALrCrL8CbS6AQXgC0QjjEEA/qqqqqqqv4AAWrixFoJAAC+eHS+Y1y+AH4pXAjelmZAAq7QknBvZIAZsHDw16dDUAE2vSl0l0eQBijP6wPN8hADv6PA2SGwpABybEbtY6YsAK4zgR7F2MIANDrMqDkzD4A2pvs/diehQBWXa9GZDapwByUNoArR6yAHjfoXogJ0kAK9WcwutNLIAJH+FPxT2fYA1vbgudnqkoAMTgyAfFLPABvu0m/1R/+AHRJjJGmAsQABqLaioLYqkAHEd0EWZSR0AL6hRv4og+gBAaP7FFOnRABS8Qu/UQwjgFKW5k3wbP1ABfCkeLQLawABtdCQVDkSUAB0KMkVrkmIAgLppVcDI1QCfOuCZ7LyEgFxh91U7sjUAFM8hmp6kvsAJFQwa0fGicAhm6FN0iWEwAcjfRskDiFwB7+fZiDbzCAGgQqmOUWqtAKeT39oltrWAfDD0g1aQWYAAsQOP2OE+YAAdodRkd7GAD+SZQrQmGogEFeCPEM2ERALrWfP/p6vsAXVrBjwyeMIAus9YMUjsPABBOmqqB3WrwD+u8DISLQFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
