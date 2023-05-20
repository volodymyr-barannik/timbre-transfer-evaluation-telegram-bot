from enum import Enum


class ExampleQuestionsStates(Enum):
    ShowExampleNumber = 1
    AskAboutSourceTimbreSimilarity = 2
    AskAboutTargetTimbreSimilarity = 3
    AskAboutSoundQuality = 4
    GoNext = 5