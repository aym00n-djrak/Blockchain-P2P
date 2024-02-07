class MinerState:
    mine = False

    @staticmethod
    def start_mining():
        MinerState.mine = True

    @staticmethod
    def stop_mining():
        MinerState.mine = False

    @staticmethod
    def is_mining():
        return MinerState.mine
