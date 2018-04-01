import sys
import markovify

def main():
    p_text = open(sys.argv[1]).read()

    print('Generating model from ' + sys.argv[1] + '...')

    m_model = markovify.Text(p_text)
    m_json = m_model.to_json()

    m_text = open(sys.argv[1] + ".mchain", 'w')
    m_text.write(m_json)
    m_text.close()

    print('Model saved as ' + sys.argv[1] + '.mchain!' )

main()
