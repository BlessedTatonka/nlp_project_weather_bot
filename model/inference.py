from .util import *
from data.prepare_data import get_data

def TestDataloader(df, batch_size, is_test=True):
    dataset = IntentsDataset(df["message"].values, None, is_test)
    dataloader = DataLoader(dataset, batch_size, shuffle=False)
    return dataloader

def _get_predictions(model, df):
    proba = []    
    model = model.eval()

    predictions = []

    data_loader = TestDataloader(df, 1)

    with torch.no_grad():
        for d in data_loader:
            
            input_ids = d["ids"].to(device)
            attention_mask = d["mask"].to(device)
            token_type_ids = d["token_type"].to(device)
            
            outputs = model(
                            input_ids,
                            attention_mask ,
                            token_type_ids
                            )
            proba.append(torch.argmax(outputs).flatten().cpu().numpy())
    return np.array(proba).flatten()


def predict_message_type(text, model):
    prediction = _get_predictions(model, pd.DataFrame({'message': [text]}))
    return labels_ord[prediction[0]]


def prepare_dataset(path="data/intents"):
    data = pd.DataFrame(columns={0, 'category'})

    for cat in glob.glob(f'{path}/*.csv'):
        cat_name = os.path.basename(cat).split('.')[0]
        tmp_data = pd.read_csv(cat, header=None)
        tmp_data['category'] = cat_name
        data = data.append(tmp_data)

    labels_ord = data['category'].unique()

    number_of_categories = len(labels_ord)
    data['label'] = data['category'].apply(lambda x: np.where(labels_ord == x)[0][0])

    return data



def train_new_model(model_name):
    model = IntentsClassifier(5)
    model.to(device)

    _, data, labels_ord = get_data()
    train(model, data, ModelConfig.NB_EPOCHS, device, 'model/' + model_name)

    return model, labels_ord

def get_labels_ord():
    return labels_ord

def load_model(model_name='best_model'):
    model = IntentsClassifier(5)
    model.load_state_dict(torch.load(model_name + '.bin'))
    model.to(device)

    return model


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
labels_ord = np.array(['get_photo', 'no_category', 'generate_photo'])

