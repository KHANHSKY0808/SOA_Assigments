from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Product
from .serializers import ProductSerializer
from .authentication import ExternalTokenAuthentication

class ProductListCreateAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # GET /products: Lấy danh sách sản phẩm
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /products: Thêm sản phẩm mới
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    # GET /products/<id>: Chi tiết sản phẩm
    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Không tìm thấy sản phẩm"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT /products/<id>: Cập nhật thông tin sản phẩm
    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Không tìm thấy sản phẩm"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE /products/<id>: Xóa sản phẩm
    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Không tìm thấy sản phẩm"}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({"message": "Đã xóa sản phẩm thành công"}, status=status.HTTP_204_NO_CONTENT)