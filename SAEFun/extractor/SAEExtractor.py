# -*- coding: utf-8 -*-
__author__ = 'LeoDong'
import cPickle as pickle

from SAECrawlers.items import UrlItem
from util import tool, config
from util.logger import log
from InfoExtractor import InfoExtractor
import os
import shutil

class SAEExtractor:
    def __init__(self):
        self.__ext_queue = {}
        self.__ie = InfoExtractor(config.path_extract_onto + "/seminar.xml", config.path_extract_onto)
        # id : item{title, url, filename, decision }
        pass

    def __auto_extract(self, ):
        pass

    def __op_new(self, data_loaded, connection):
        item_id = int(data_loaded['id'])
        item = UrlItem.load_with_content(id=item_id, file_path=config.path_extractor_inbox)

        # # 检查是否有已经能用(且有效)的extractor,有的话:
        # rule_id = 35
        # # 否则:
        rule_id = -1

        self.__ext_queue[item_id] = {
            "title": item['title'],
            "url": item['url'],
            "filename": item.filename(),
            "decision": item['is_target'],
            "rule_id": rule_id
        }

        log.info("[%s]: # %s " % (item_id, rule_id))

        pass

    def __op_list(self, data_loaded, connection):
        tool.send_msg(connection, pickle.dumps(self.__ext_queue, -1))
        pass

    def __op_maps(self, data_loaded, connection):
        tool.send_msg(connection, pickle.dumps({'rule':self.__ie.map(),'action':self.__ie.action_map()}, -1))
        pass

    def __op_preview(self, data_loaded, connection):
        preview = {
            1: {
                'name': 'title',
                'value': '',
            },
            2: {
                'name': 'location',
                'value': '',
            }
        }
        tool.send_msg(connection, pickle.dumps(preview, -1))
        pass

    def __op_rejudge_done(self, data_loaded, connection):
        item_id = int(data_loaded['id'])
        decision = int(data_loaded['decision'])
        item = UrlItem.load(id=item_id)
        del self.__ext_queue[item_id]
        self.__send_back_to_judge(item,decision)
        tool.send_msg(connection, "0")
        pass

    def __op_test_rule(self, data_loaded, connection):
        item_id = int(data_loaded['id'])
        rule = data_loaded['rule']
        attrid = data_loaded['attrid']
        item = UrlItem.load_with_content(id=item_id,file_path=config.path_extractor_inbox)
        tool.send_msg(
            connection,
            self.__ie.extract_attr(item,rule_id_or_dict=rule,attr_id=attrid)
        )
        pass

    def __op_add_rule(self, data_loaded, connection):
        rule = data_loaded['rule']
        attrid = data_loaded['attrid']
        self.__ie.add_rule(attrid,rule)
        tool.send_msg(
            connection,
            "0"
        )
        pass

    def __op_test_extractor(self, data_loaded, connection):
        item_id = int(data_loaded['id'])
        extractor = data_loaded['extractor']
        # attrid = data_loaded['attrid']
        # item = UrlItem.load_with_content(id=item_id,file_path=config.path_extractor_inbox)
        # tool.send_msg(
        #     connection,
        #     self.__ie.extract_attr(item,rule_id_or_dict=rule,attr_id=attrid)
        # )
        pass

    def __op_add_extractor(self, data_loaded, connection):
        item_id = int(data_loaded['id'])
        extractor = data_loaded['extractor']
        # self.__ie.add_rule(attrid,rule)
        # tool.send_msg(
        #     connection,
        #     "0"
        # )
        pass

    @staticmethod
    def __operations(cmd):
        maps = {
            config.socket_CMD_extractor_new: SAEExtractor.__op_new,
            config.socket_CMD_extractor_list: SAEExtractor.__op_list,
            config.socket_CMD_extractor_maps: SAEExtractor.__op_maps,
            config.socket_CMD_extractor_preview: SAEExtractor.__op_preview,
            config.socket_CMD_extractor_rejudge_done: SAEExtractor.__op_rejudge_done,
            config.socket_CMD_extractor_test_rule: SAEExtractor.__op_test_rule,
            config.socket_CMD_extractor_add_rule: SAEExtractor.__op_add_rule,
            config.socket_CMD_extractor_test_extractor: SAEExtractor.__op_test_extractor,
            config.socket_CMD_extractor_add_extract: SAEExtractor.__op_add_extractor,
        }
        return maps[cmd]

    @staticmethod
    def __send_back_to_judge(item,decision):
        # move file
        shutil.move(config.path_extractor_inbox + "/%s" % item.filename(),
                    config.path_judge_inbox + "/%s" % item.filename())

        # SIGNAL
        data = {"operation": config.socket_CMD_judge_new,"id": item['id'], "decision": decision}
        data_string = pickle.dumps(data, -1)
        tool.send_message(data_string, config.socket_addr_judge)

    def process(self, connection, client_address):
        try:
            data = tool.recv_msg(connection)
            data_loaded = pickle.loads(data)
            log.debug('new connection from %s', client_address)
            log.debug("data received: %s", data_loaded)
            self.__operations(data_loaded['operation'])(self, data_loaded, connection)
        finally:
            # Clean up the connection
            log.debug('connection closed for %s', client_address)
            connection.close()
