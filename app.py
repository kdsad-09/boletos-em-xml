import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Leitor de Boletos de NFe", layout="wide")

st.title("Leitor de Parcelas de NFe (Lote ZIP)")
st.write("Envie um arquivo .ZIP contendo as NFe em XML para extrair o emitente, número de parcelas, valores e vencimentos.")

uploaded_file = st.file_uploader("Selecione o arquivo .ZIP", type=["zip"])

def processar_xmls_zip(zip_file):
    dados_faturas = []
    
    with zipfile.ZipFile(zip_file, 'r') as z:
        for file_info in z.infolist():
            if file_info.filename.lower().endswith('.xml'):
                try:
                    xml_content = z.read(file_info.filename)
                    root = ET.fromstring(xml_content)
                    
                    # Trata o namespace do XML da NFe se existir
                    namespace = ''
                    if root.tag.startswith('{'):
                        namespace = root.tag.split('}')[0] + '}'
                    
                    # Nome do Emitente (Razão Social ou Nome Fantasia)
                    emitente_node = root.find(f".//{namespace}emit/{namespace}xNome")
                    emitente = emitente_node.text if emitente_node is not None else "Não informado"
                    
                    # Chave/Número da Nota para identificação
                    ide_node = root.find(f".//{namespace}ide/{namespace}nNF")
                    numero_nota = ide_node.text if ide_node is not None else "N/A"
                    
                    # Busca todas as duplicatas/parcelas
                    duplicatas = root.findall(f".//{namespace}cobr/{namespace}dup")
                    qtd_parcelas = len(duplicatas)
                    
                    if qtd_parcelas > 0:
                        for dup in duplicatas:
                            n_dup_node = dup.find(f"{namespace}nDup")
                            v_enc_node = dup.find(f"{namespace}dVenc")
                            v_dup_node = dup.find(f"{namespace}vDup")
                            
                            parcela_num = n_dup_node.text if n_dup_node is not None else "1"
                            vencimento = v_enc_node.text if v_enc_node is not None else "N/A"
                            valor = float(v_dup_node.text) if v_dup_node is not None else 0.0
                            
                            dados_faturas.append({
                                "Emitente": emitente,
                                "Nº Nota": numero_nota,
                                "Qtd Parcelas Total": qtd_parcelas,
                                "Nº Parcela": parcela_num,
                                "Vencimento": vencimento,
                                "Valor (R$)": valor
                            })
                    else:
                        # Registro para notas sem parcela/boletos cobrados na tag cobr
                        dados_faturas.append({
                            "Emitente": emitente,
                            "Nº Nota": numero_nota,
                            "Qtd Parcelas Total": 0,
                            "Nº Parcela": "Sem parcela",
                            "Vencimento": "À vista / Sem cobrança",
                            "Valor (R$)": 0.0
                        })
                except Exception as e:
                    st.warning(f"Erro ao processar o arquivo {file_info.filename}: {e}")
                    
    return pd.DataFrame(dados_faturas)

if uploaded_file is not None:
    df = processar_xmls_zip(uploaded_file)
    
    if not df.empty:
        st.subheader("Resultados Encontrados")
        st.dataframe(df, use_container_width=True)
        
        # Opção para baixar em CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar Tabela em CSV",
            data=csv,
            file_name="parcelas_nfe.csv",
            mime="text/csv"
        )
    else:
        st.error("Nenhum arquivo XML válido foi encontrado dentro do arquivo ZIP enviado.")
