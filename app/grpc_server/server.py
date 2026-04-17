import grpc
from concurrent import futures
import time
from app.grpc_server import ia_service_pb2
from app.grpc_server import ia_service_pb2_grpc
from app.agents.cv_parser import CVParserAgent

class AIServiceServicer(ia_service_pb2_grpc.AIServiceServicer):
    def __init__(self):
        self.cv_parser = CVParserAgent()

    def ParseCV(self, request, context):
        try:
            parsed_cv = self.cv_parser.parse(request.cv_text)
            return ia_service_pb2.CVResponse(json_data=parsed_cv.model_dump_json())
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ia_service_pb2.CVResponse()

    def GetInstantMatch(self, request, context):
        # Placeholder para o agente de match
        return ia_service_pb2.MatchResponse(score=0.85, reasoning="Match simulado via gRPC")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ia_service_pb2_grpc.add_AIServiceServicer_to_server(AIServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC Server started on port 50051")
    server.start()
    return server
