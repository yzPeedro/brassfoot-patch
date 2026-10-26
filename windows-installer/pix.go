package main

// Payload EMV Pix voluntário fornecido pelo mantenedor. Não contém valor fixo,
// não cria cobrança e não requer conexão de rede nem dados do usuário.
const pixPayload = "00020126970014BR.GOV.BCB.PIX0136dd20e247-c861-44a1-9a21-2ddb827465e90235Ajude seu amiguinho a tomar um café5204000053039865802BR5925Pedro Henrique Pessoa Cru6009SAO PAULO62140510WP4lJ5p0Ib630482B0"

// QR com correção M e quiet zone de 4 módulos. Gerado localmente do
// pixPayload (61x61 bits, row-major, MSB-first). Não chamar APIs externas.
const pixQRSize = 61
const pixQRBitsBase64 = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP44kHkaY/gEEDJ0lxOQQC6rCNo79LoBdWtZKB7V0Auo1Q+/6i6AQW8vRT6xBAP6qqqqqq/gABaMMQkmAAC+bb38HyPgBQHXIYICaYAtkl00cuk0AOHaiUizH6AKNX3NqneDAH770tnpS9gAHEsZ243xQB0OgxtqddAA9oFFXCfDGAXEoibdyySAK/qTDALu5ADQA1tUgt0wAKn+eX2IPwA6J94Yq/CsAz0Cm/sJkOAahPcUGGxRAH+6Qv0G/5gHRTUsV+jEgBq0a2sLUqYBUVZHEpLRAAz9G//S9vkADMOcpbxbWAKouZHHlK1AGDNys00EFgDTUhWZL/ywBEP0pLygTMAomGMliem+AclDzYTzURAPbm/aYnTpAE40cNSteEQCa/1oejFDgBeWcb9SCdIA7uoNJls+8AaM2W3Mix3AN8671bQ1hADA6IX9swyQASeo74jS/4AARZBFdDRkA/kl0r37KmAQUUCRDi8QALrXpP69f5AF1ScsFLPgAC6wIlSadXQBBFqTYocicA/oqier5mMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
