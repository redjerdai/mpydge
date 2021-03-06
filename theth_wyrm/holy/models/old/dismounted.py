
#
class Helium:
    """
    Model architecture:

        -- Embedding
        -- EmbeddingDrop
        -- Preprocessor

        == LAYER X: -- Semi-Linear with Temperature factor
                    -- Activator (in the article it is SoftMax)
                    -- Interprocessor (optional)
                    -- Interdrop      (optional)

    Idea:
           The article (in it's part considering softmax binning function) describes how to compute bins for
           only one variable. Data usually contains many fields, but Decision Tree Cell splits only through one
           of them and the selection is another parameter to be estimated. So we will embed it!
    """

    def __init__(self, data, layers_dimensions, tau,
                 activators, preprocessor=nn.BatchNorm1d, embeddingdrop=0.0, activators_args={}, interprocessors=None,
                 interdrops=None, postlayer=None):

        self.data = data

        self.epochs = None
        self.aggregated_losses = None
        self.validation_losses = None

        if data.data_frame.categorical_embeddings is not None:
            self.all_embeddings = nn.ModuleList([nn.Embedding(ni, nf) for ni, nf in data.data_frame.categorical_embeddings])
            if preprocessor is not None:
                self.batch_norm_num = preprocessor(data.data_frame.numerical_shape)
            self.embedding_dropout = nn.Dropout(embeddingdrop)
            num_categorical_cols = sum((nf for ni, nf in data.data_frame.categorical_embeddings))
        else:
            self.all_embeddings = None
            num_categorical_cols = 0

        all_layers = []
        num_numerical_cols = data.data_frame.numerical_shape
        input_size = num_categorical_cols + num_numerical_cols

        if not isinstance(tau, list):
            tau = [tau] * len(layers_dimensions)
        if not isinstance(activators, list):
            activators = [activators] * len(layers_dimensions)
        if not isinstance(activators_args, list):
            activators_args = [activators_args] * len(layers_dimensions)
        if interprocessors is not None and not isinstance(interprocessors, list):
            interprocessors = [interprocessors] * len(layers_dimensions)
        if interdrops is not None and not isinstance(interdrops, list):
            interdrops = [interdrops] * len(layers_dimensions)

        for j in range(len(layers_dimensions)):
            all_layers.append(SemiLinearTemperatured(input_size, layers_dimensions[j], tau[j]))
            all_layers.append(activators[j](**activators_args[j]))
            if interprocessors is not None:
                all_layers.append(interprocessors[j](layers_dimensions[j]))
            if interdrops is not None:
                all_layers.append(nn.Dropout(interdrops[j]))
            input_size = layers_dimensions[j]

        if postlayer is not None:
            all_layers.append(postlayer(layers_dimensions[-1], data.data_frame.n_classes))

        self.layers = nn.Sequential(*all_layers)

    def forward(self, x_categorical, x_numerical):
        if self.data.data_frame.categorical_embeddings is not None:
            embeddings = []
            for i, e in enumerate(self.all_embeddings):
                embeddings.append(e(x_categorical[:, i]))
            x_embedding = torch.cat(embeddings, 1)
            x_embedding = self.embedding_dropout(x_embedding)
        else:
            x_embedding = None

        if self.data.data_frame.categorical_embeddings is not None and self.data.data_frame.numerical_shape is not None:
            x = torch.cat([x_embedding, x_numerical], 1)
        if self.data.data_frame.categorical_embeddings is None and self.data.data_frame.numerical_shape is not None:
            x = torch.cat([x_numerical], 1)
        if self.data.data_frame.categorical_embeddings is not None and self.data.data_frame.numerical_shape is None:
            x = torch.cat([x_embedding], 1)

        x = self.layers(x)
        return x

    def fit(self, optimiser, loss_function, epochs=500):

        self.epochs = epochs
        self.aggregated_losses = []
        self.validation_losses = []

        for i in range(epochs):
            i += 1
            for phase in ['train', 'validate']:

                if phase == 'train':
                    y_pred = self(self.data.data_frame.train.categorical, self.data.data_frame.train.numerical)
                    single_loss = loss_function(y_pred, self.data.data_frame.train.output)
                else:
                    y_pred = self(self.data.data_frame.validation.categorical, self.data.data_frame.validation.numerical)
                    single_loss = loss_function(y_pred, self.data.data_frame.validation.output)

                optimiser.zero_grad()

                if phase == 'train':
                    train_lost = single_loss.item()
                    self.aggregated_losses.append(single_loss)
                    single_loss.backward()
                    optimiser.step()
                else:
                    validation_lost = single_loss.item()
                    self.validation_losses.append(single_loss)

            if i % 25 == 1:
                print('epoch: {0:3} train loss: {1:10.8f} validation loss: {2:10.8f}'.format(i, train_lost,
                                                                                             validation_lost))
        print('epoch: {0:3} train loss: {1:10.8f} validation loss: {2:10.8f}'.format(i, train_lost, validation_lost))

    def fit_plot(self):

        pyplot.plot(numpy.array(numpy.arange(self.epochs)), self.aggregated_losses, label='Train')
        pyplot.plot(numpy.array(numpy.arange(self.epochs)), self.validation_losses, label='Validation')
        pyplot.legend(loc="upper left")
        pyplot.show()

    def predict(self):

        output = self(self.data.data_frame.test.categorical, self.data.data_frame.test.numerical)
        result = numpy.argmax(output.detach().numpy(), axis=1)

        return result

    def summary(self, on='test', loss_function=None, show_confusion_matrix=True,
                report=False, score=None):

        if on == 'train':

            y_val = self(self.data.data_frame.train.categorical, self.data.data_frame.train.numerical)
            y_hat = self.predict()
            y = self.data.data_frame.test.output.detach().numpy()

            if loss_function is not None:
                print('{0:25}: {1:10.8f}'.format(str(loss_function)[:-2],
                                                 loss_function(y_val, self.data.data_frame.test.output)))

        if on == 'validation':

            y_val = self(self.data.data_frame.validation.categorical, self.data.data_frame.validation.numerical)
            y_hat = self.predict()
            y = self.data.data_frame.validation.output.detach().numpy()

            if loss_function is not None:
                print('{0:25}: {1:10.8f}'.format(str(loss_function)[:-2],
                                                 loss_function(y_val, self.data.data_frame.validation.output)))

        if on == 'test':

            y_val = self(self.data.data_frame.test.categorical, self.data.data_frame.test.numerical)
            y_hat = self.predict()
            y = self.data.data_frame.test.output.detach().numpy()

            if loss_function is not None:
                print('{0:25}: {1:10.8f}'.format(str(loss_function)[:-2],
                                                 loss_function(y_val, self.data.data_frame.test.output)))

        if show_confusion_matrix:
            seaborn.heatmap(confusion_matrix(y, y_hat), annot=True)

        if report:
            print(classification_report(y, y_hat))